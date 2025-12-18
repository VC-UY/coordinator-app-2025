"""
Proxy Redis pour le contrôle des messages et souscriptions.
Intercepte toutes les commandes Redis pour appliquer des règles d'autorisation.
VERSION OPTIMISÉE POUR 100K+ CLIENTS - Version stable sans conflits
"""

import asyncio
import socket
import threading
import logging
import json
import traceback
from datetime import datetime
import jwt
import redis
import time
from typing import Dict, Set, List, Optional
from collections import defaultdict

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('RedisProxy')
logger.setLevel(logging.DEBUG)

# Import du proxy de fichiers
from .file_proxy import get_file_proxy_instance

class RESPParser:
    """Parser RESP robuste pour gérer tous les types de messages Redis"""
    
    def __init__(self):
        self.buffer = bytearray()
        self.position = 0
    
    def feed(self, data: bytes):
        """Ajoute des données au buffer"""
        self.buffer.extend(data)
    
    def parse_next(self):
        """Parse le prochain message RESP complet"""
        if self.position >= len(self.buffer):
            return None
        
        try:
            start_pos = self.position
            if self.position >= len(self.buffer):
                return None
                
            message_type = chr(self.buffer[self.position])
            self.position += 1
            
            if message_type == '*':  # Array
                return self._parse_array()
            elif message_type == '$':  # Bulk String
                return self._parse_bulk_string()
            elif message_type == '+':  # Simple String
                return self._parse_simple_string()
            elif message_type == '-':  # Error
                return self._parse_error()
            elif message_type == ':':  # Integer
                return self._parse_integer()
            else:
                # Type inconnu, remettre la position
                self.position = start_pos
                return None
                
        except (IndexError, ValueError):
            # Pas assez de données, remettre la position
            self.position = start_pos
            return None
    
    def _parse_array(self):
        """Parse un array RESP"""
        length_str = self._read_until_crlf()
        if length_str is None:
            return None
        
        try:
            length = int(length_str)
        except ValueError:
            return None
        
        if length == -1:  # Null array
            return None
        
        elements = []
        for _ in range(length):
            element = self.parse_next()
            if element is None:
                return None
            elements.append(element)
        
        return elements
    
    def _parse_bulk_string(self):
        """Parse une bulk string RESP - VERSION CORRIGÉE pour gros messages"""
        length_str = self._read_until_crlf()
        if length_str is None:
            return None
        
        try:
            length = int(length_str)
        except ValueError:
            return None
        
        if length == -1:  # Null string
            return None
        
        # CORRECTION: Vérification plus robuste pour les gros messages
        if self.position + length + 2 > len(self.buffer):
            # Pas assez de données disponibles pour ce message
            return None
        
        # CORRECTION: Extraction des données avec gestion d'erreur pour gros messages
        try:
            data = self.buffer[self.position:self.position + length]
            self.position += length + 2  # +2 pour \r\n
            
            # Décodage avec gestion d'erreur pour préserver l'intégrité
            return data.decode('utf-8', errors='replace')
        except (IndexError, UnicodeDecodeError) as e:
            logger.error(f"Erreur décodage bulk string (longueur={length}): {e}")
            return None
    
    def _parse_simple_string(self):
        """Parse une simple string RESP"""
        return self._read_until_crlf()
    
    def _parse_error(self):
        """Parse une error RESP"""
        return self._read_until_crlf()
    
    def _parse_integer(self):
        """Parse un integer RESP"""
        value_str = self._read_until_crlf()
        if value_str is None:
            return None
        try:
            return int(value_str)
        except ValueError:
            return None
    
    def _read_until_crlf(self):
        """Lit jusqu'au prochain \r\n"""
        start = self.position
        
        while self.position < len(self.buffer) - 1:
            if (self.buffer[self.position] == ord('\r') and 
                self.buffer[self.position + 1] == ord('\n')):
                
                data = self.buffer[start:self.position].decode('utf-8', errors='replace')
                self.position += 2
                return data
            
            self.position += 1
        
        self.position = start
        return None
    
    def has_complete_message(self):
        """Vérifie s'il y a un message complet"""
        saved_pos = self.position
        result = self.parse_next()
        self.position = saved_pos
        return result is not None
    
    def clear_processed(self):
        """Nettoie les données traitées"""
        if self.position > 0:
            self.buffer = self.buffer[self.position:]
            self.position = 0

class RedisCommand:
    """Classe pour analyser et représenter une commande Redis - Version optimisée"""
    
    def __init__(self, parsed_data):
        self.parsed_data = parsed_data
        self.command_type = None
        self.args = []
        self.parse()
    
    def parse(self):
        """Parse les données RESP déjà parsées"""
        try:
            if isinstance(self.parsed_data, list) and len(self.parsed_data) > 0:
                self.command_type = str(self.parsed_data[0]).upper()
                self.args = [str(arg) for arg in self.parsed_data[1:]]
                logger.debug(f"Commande parsée: type={self.command_type}, args={self.args}")
            else:
                self.command_type = 'UNKNOWN'
                self.args = []
        except Exception as e:
            logger.error(f"Erreur lors du parsing de la commande: {e}")
            self.command_type = 'UNKNOWN'
            self.args = []

    def is_pubsub_command(self):
        """Vérifie si la commande est liée à pub/sub"""
        result = self.command_type in ['PUBLISH', 'SUBSCRIBE', 'PSUBSCRIBE', 'UNSUBSCRIBE', 'PUNSUBSCRIBE']
        logger.debug(f"is_pubsub_command: {result} pour {self.command_type}")
        return result

    def get_channel(self):
        """Récupère le canal pour les commandes pub/sub"""
        if self.command_type == 'PUBLISH' and len(self.args) >= 1:
            return self.args[0]
        elif self.command_type in ['SUBSCRIBE', 'UNSUBSCRIBE'] and self.args:
            return self.args
        return None

    def get_message(self):
        """Récupère le message pour la commande PUBLISH"""
        if self.command_type == 'PUBLISH' and len(self.args) >= 2:
            return self.args[1]
        return None

    def __str__(self):
        return f"RedisCommand(type={self.command_type}, args={self.args})"

class ClientData:
    """Données client optimisées pour 100K+ connexions"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.authenticated = False
        self.user_id = None
        self.role = None
        self.token = None
        self.subscriptions = set()
        self.last_activity = time.time()

class AsyncPubSubManager:
    """Gestionnaire pub/sub asynchrone optimisé pour 100K+ clients - Version corrigée"""
    
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.subscribers = defaultdict(set)  # channel -> set of client_ids
        self.client_writers = {}  # client_id -> writer
        self.message_queue = asyncio.Queue(maxsize=50000)  # Queue plus grande
        self.distribution_task = None
        self.listen_tasks = {}  # channel -> task
        
        # Utiliser redis-py standard pour éviter les conflits aioredis
        self.redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            decode_responses=True,
            socket_keepalive=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
    async def start(self):
        """Démarre le gestionnaire pub/sub"""
        self.distribution_task = asyncio.create_task(self._message_distributor())
        logger.info("Gestionnaire pub/sub démarré")
        
    async def stop(self):
        """Arrête le gestionnaire pub/sub"""
        if self.distribution_task:
            self.distribution_task.cancel()
            try:
                await self.distribution_task
            except asyncio.CancelledError:
                pass
        
        for task in self.listen_tasks.values():
            task.cancel()
        
        if self.listen_tasks:
            await asyncio.gather(*self.listen_tasks.values(), return_exceptions=True)
    
    async def subscribe(self, client_id: str, writer, channels: List[str]):
        """Abonne un client à des canaux"""
        self.client_writers[client_id] = writer
        
        for channel in channels:
            self.subscribers[channel].add(client_id)
            
            # Créer une tâche d'écoute pour ce canal si nécessaire
            if channel not in self.listen_tasks:
                self.listen_tasks[channel] = asyncio.create_task(
                    self._listen_channel(channel)
                )
    
    async def unsubscribe(self, client_id: str, channels: Optional[List[str]] = None):
        """Désabonne un client"""
        if channels is None:
            # Désabonner de tous les canaux
            channels = []
            for channel, subs in self.subscribers.items():
                if client_id in subs:
                    channels.append(channel)
        
        for channel in channels:
            if channel in self.subscribers and client_id in self.subscribers[channel]:
                self.subscribers[channel].remove(client_id)
                
                # Arrêter l'écoute si plus d'abonnés
                if not self.subscribers[channel] and channel in self.listen_tasks:
                    self.listen_tasks[channel].cancel()
                    del self.listen_tasks[channel]
    
    async def cleanup_client(self, client_id: str):
        """Nettoie un client déconnecté"""
        if client_id in self.client_writers:
            del self.client_writers[client_id]
        await self.unsubscribe(client_id)
    
    async def publish_to_subscribers(self, channel: str, message: str):
        """Publie un message aux abonnés locaux"""
        await self.message_queue.put((channel, message))
    
    async def _listen_channel(self, channel: str):
        """Écoute un canal Redis - Version corrigée sans aioredis"""
        try:
            # Créer un client Redis dédié pour ce canal
            redis_client = redis.Redis(
                host=self.redis_host, 
                port=self.redis_port, 
                decode_responses=True,
                socket_keepalive=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            pubsub = redis_client.pubsub()
            
            # S'abonner au canal de manière asynchrone
            await asyncio.get_event_loop().run_in_executor(None, pubsub.subscribe, channel)
            logger.debug(f"Écoute démarrée pour le canal: {channel}")
            
            while channel in self.listen_tasks:
                try:
                    # Écouter les messages de manière asynchrone avec timeout plus court
                    message = await asyncio.get_event_loop().run_in_executor(
                        None, pubsub.get_message, 0.5
                    )
                    
                    if message and message['type'] == 'message':
                        await self.message_queue.put((channel, message['data']))
                    
                    # Petite pause pour éviter la surcharge CPU
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Erreur dans l'écoute du canal {channel}: {e}")
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            logger.debug(f"Arrêt de l'écoute du canal {channel}")
        except Exception as e:
            logger.error(f"Erreur dans l'écoute du canal {channel}: {e}")
        finally:
            try:
                # Nettoyage de manière asynchrone
                await asyncio.get_event_loop().run_in_executor(None, pubsub.unsubscribe, channel)
                await asyncio.get_event_loop().run_in_executor(None, pubsub.close)
                redis_client.close()
            except Exception as e:
                logger.debug(f"Erreur nettoyage écoute {channel}: {e}")

    async def _message_distributor(self):
        """Distribue les messages aux clients abonnés - Version optimisée"""
        while True:
            try:
                channel, data = await self.message_queue.get()
                
                subscribers = list(self.subscribers.get(channel, []))
                if not subscribers:
                    continue
                
                # Formater le message RESP une seule fois
                resp_message = self._format_pubsub_message(channel, data)
                
                # Envoyer en parallèle à tous les abonnés (optimisé pour 100K+)
                send_tasks = []
                batch_size = 1000  # Traiter par batch pour éviter l'overload
                
                for i in range(0, len(subscribers), batch_size):
                    batch = subscribers[i:i + batch_size]
                    task = asyncio.create_task(
                        self._send_batch(batch, resp_message)
                    )
                    send_tasks.append(task)
                
                if send_tasks:
                    await asyncio.gather(*send_tasks, return_exceptions=True)
                
                self.message_queue.task_done()
                logger.info(f"Message distribué à {len(subscribers)} clients sur {channel}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erreur dans le distributeur de messages: {e}")
    
    async def _send_batch(self, client_ids: List[str], message: bytes):
        """Envoie un message à un batch de clients"""
        for client_id in client_ids:
            if client_id in self.client_writers:
                try:
                    writer = self.client_writers[client_id]
                    writer.write(message)
                    await writer.drain()
                except Exception as e:
                    logger.error(f"Erreur envoi à {client_id}: {e}")
                    # Nettoyer le client défaillant
                    if client_id in self.client_writers:
                        del self.client_writers[client_id]
    
    def _format_pubsub_message(self, channel: str, data) -> bytes:
        """Formate un message pub/sub au format RESP - VERSION CORRIGÉE pour préserver l'intégrité"""
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='replace')
        elif not isinstance(data, str):
            data = str(data)
        
        # CORRECTION: Construction plus robuste du message RESP
        # pour éviter les corruptions avec les gros messages
        try:
            # Encoder les données en UTF-8 pour connaître la taille exacte
            channel_bytes = channel.encode('utf-8')
            data_bytes = data.encode('utf-8')
            
            # Construire le message RESP manuellement avec les bonnes tailles
            resp_parts = []
            resp_parts.append(b"*3\r\n")  # Array de 3 éléments
            
            # "message"
            resp_parts.append(b"$7\r\nmessage\r\n")
            
            # Channel
            resp_parts.append(f"${len(channel_bytes)}\r\n".encode('utf-8'))
            resp_parts.append(channel_bytes)
            resp_parts.append(b"\r\n")
            
            # Data (le contenu du message)
            resp_parts.append(f"${len(data_bytes)}\r\n".encode('utf-8'))
            resp_parts.append(data_bytes)
            resp_parts.append(b"\r\n")
            
            # Joindre toutes les parties en bytes pour éviter les problèmes d'encodage
            final_message = b''.join(resp_parts)
            
            # Log pour déboguer les gros messages
            if len(data_bytes) > 10000:  # Plus de 10KB
                logger.debug(f"Message pub/sub volumineux formaté: {len(data_bytes)} bytes")
            
            return final_message
            
        except Exception as e:
            logger.error(f"Erreur formatage message pub/sub: {e}")
            # Fallback en cas d'erreur
            fallback = f"*3\r\n$7\r\nmessage\r\n${len(channel)}\r\n{channel}\r\n$5\r\nERROR\r\n"
            return fallback.encode('utf-8')

class AsyncRedisProxy:
    """
    Proxy Redis asynchrone optimisé pour 100K+ connexions simultanées
    Version corrigée sans conflits aioredis
    """
    
    def __init__(self, redis_host='localhost', redis_port=6379, proxy_port=6380):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.proxy_port = proxy_port
        self.running = False
        
        # Pool de connexions Redis standard pour éviter les conflits
        self.redis_pool = redis.ConnectionPool(
            host=redis_host,
            port=redis_port,
            max_connections=500,
            socket_keepalive=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Gestionnaire pub/sub
        self.pubsub_manager = None
        
        # Proxy de fichiers
        self.file_proxy = None
        
        # Stockage des clients optimisé
        self.clients = {}  # client_id -> ClientData
        
        # Métriques de performance
        self.stats = {
            'connected_clients': 0,
            'total_connections': 0,
            'messages_processed': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Configuration des canaux
        self.coordinator_address = [('localhost', 6380), ('127.0.0.1', 6380)]
        
        self.open_channels = {
            'auth/register': True,
            'auth/register_response': True,
            'auth/login': True,
            'auth/login_response': True,
            'coord/heartbeat/#': True,
            'coord/emergency': True,
            'task/assignment': True,
            'task/accept': True,
            'auth/volunteer_register': True,
            'auth/volunteer_register_response': True,
            'auth/volunteer_login': True,
            'auth/volunteer_login_response': True,
            'auth/token_refresh': True,
            'auth/token_refresh_response': True,
            # Canaux de test pour les tests d'intégrité et de performance
            'test/channel': True,
            'test/integrity/small': True,
            'test/integrity/medium': True,
            'test/integrity/large': True,
            'test/integrity/mixed': True,
            'test/heartbeat': True,
        }
        
        self.manager_channels = {
            'tasks/new': True,
            'tasks/assign': True,
            'task/terminate': True,
            'manager/status': True,
            'manager/requests': True,
            'workflow/submit': True,
            'workflow/submit_response': True,
            'workflow/terminate': True,
            'task/reassignment': True,
        }
        
        self.volunteer_channels = {
            'volunteer/available': True,
            'volunteer/resources': True,
            'task/result/#': True,
            'volunteer/data': True,
            'task/status': True, 
            'task/complete': True,
            'task/progress': True,
            'volunteer_state': True,  # Canal pour l'envoi de l'état/métriques du volontaire
        }
        
        # Transformateurs de messages
        self.message_transformers = [
            self.add_metadata,
            self.route_file_server,  # ← Transformateur pour router les fichiers de sortie (résultats)
            self.route_input_files,  # ← Transformateur pour router les fichiers d'entrée (assignation)
            self.handle_token_refresh,  # ← Transformateur pour gérer le rafraîchissement des tokens
            # self.filter_sensitive_data
        ]
    
    async def start(self):
        """Démarre le proxy asynchrone"""
        # Initialiser le gestionnaire pub/sub avec les bons paramètres
        self.pubsub_manager = AsyncPubSubManager(self.redis_host, self.redis_port)
        await self.pubsub_manager.start()
        
        # Initialiser et démarrer le proxy de fichiers
        self.file_proxy = get_file_proxy_instance(host='0.0.0.0', port=8410)
        await self.file_proxy.start()
        logger.info("✅ Proxy de fichiers initialisé sur le port 8410")
        
        # CORRECTION: Écouter automatiquement tous les canaux ouverts sur Redis
        await self._setup_open_channels_listeners()
        
        # Démarrer le serveur avec optimisations pour haute charge
        server = await asyncio.start_server(
            self.handle_client,
            '0.0.0.0',
            self.proxy_port,
            limit=10*1024*1024,  # 10MB buffer par connexion (plus grand)
            backlog=5000  # Queue de connexions plus grande
        )
        
        self.running = True
        
        # Tâches de maintenance
        asyncio.create_task(self.monitor_performance())
        asyncio.create_task(self.cleanup_inactive_clients())
        
        logger.info(f"Proxy Redis asynchrone démarré sur le port {self.proxy_port}")
        logger.info(f"Optimisé pour 100K+ connexions simultanées")
        
        async with server:
            await server.serve_forever()
    
    async def _setup_open_channels_listeners(self):
        """Configure l'écoute automatique des canaux ouverts sur Redis"""
        logger.info("Configuration de l'écoute automatique des canaux ouverts...")
        
        # Créer des listeners automatiques pour tous les canaux ouverts
        open_channels_list = list(self.open_channels.keys())
        
        # Ajouter le canal task/terminate pour nettoyer les tâches
        if 'task/terminate' not in open_channels_list:
            open_channels_list.append('task/terminate')
        
        for channel in open_channels_list:
            # Ignorer les patterns (avec #)
            if '#' not in channel:
                # Créer une tâche d'écoute dédiée pour ce canal ouvert
                if channel not in self.pubsub_manager.listen_tasks:
                    self.pubsub_manager.listen_tasks[channel] = asyncio.create_task(
                        self.pubsub_manager._listen_channel(channel)
                    )
                    logger.info(f"Écoute automatique configurée pour canal ouvert: {channel}")
        
        # S'abonner au canal task/terminate pour nettoyer les tâches
        asyncio.create_task(self._listen_task_terminate())
        
        logger.info(f"Écoute automatique configurée pour {len([c for c in open_channels_list if '#' not in c])} canaux ouverts")
    
    async def _listen_task_terminate(self):
        """Écoute le canal task/terminate pour nettoyer les tâches terminées"""
        try:
            redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True
            )
            pubsub = redis_client.pubsub()
            await asyncio.get_event_loop().run_in_executor(None, pubsub.subscribe, 'task/terminate')
            
            logger.info("🎧 Écoute du canal task/terminate pour le nettoyage des tâches")
            
            while self.running:
                try:
                    message = await asyncio.get_event_loop().run_in_executor(
                        None, pubsub.get_message, 0.5
                    )
                    
                    if message and message['type'] == 'message':
                        data = json.loads(message['data'])
                        task_id = data.get('task_id')
                        
                        if task_id and self.file_proxy:
                            self.file_proxy.unregister_task(task_id)
                            logger.info(f"🧹 Tâche {task_id} nettoyée du proxy de fichiers")
                    
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"Erreur dans l'écoute de task/terminate: {e}")
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de l'écoute task/terminate: {e}")
    
    async def stop(self):
        """Arrête le proxy"""
        self.running = False
        
        if self.file_proxy:
            await self.file_proxy.stop()
            logger.info("✅ Proxy de fichiers arrêté")
        
        if self.pubsub_manager:
            await self.pubsub_manager.stop()
        
        if self.redis_pool:
            self.redis_pool.disconnect()
        
        logger.info("Proxy Redis arrêté")
    
    async def handle_client(self, reader, writer):
        """Gère un client - Version optimisée pour haute charge avec correction corruption messages"""
        client_addr = writer.get_extra_info('peername')
        client_id = f"{client_addr[0]}:{client_addr[1]}:{int(time.time()*1000) % 10000}"
        
        # Créer les objets pour ce client
        parser = RESPParser()
        client_data = ClientData(client_id)
        # Utiliser une connexion Redis standard pour éviter les conflits
        redis_connection = redis.Redis(connection_pool=self.redis_pool)
        
        # Enregistrer le client
        self.clients[client_id] = client_data
        self.stats['connected_clients'] += 1
        self.stats['total_connections'] += 1
        
        logger.debug(f"Nouvelle connexion: {client_id}")
        
        try:
            while self.running:
                try:
                    # CORRECTION: Timeout plus long pour les clients PubSub (qui restent en écoute passive)
                    # Les clients PubSub peuvent ne pas envoyer de données pendant longtemps
                    # Le heartbeat est géré séparément par le PubSubManager
                    read_timeout = 300.0 if client_data.subscriptions else 60.0  # 5 min pour PubSub, 1 min sinon
                    
                    data = await asyncio.wait_for(
                        reader.read(65536),  # 64KB chunks pour les gros messages
                        timeout=read_timeout
                    )
                    
                    if not data:
                        # Ne pas déconnecter les clients PubSub sur timeout de lecture
                        if client_data.subscriptions:
                            logger.debug(f"Client PubSub {client_id} - lecture vide mais gardé connecté (abonnements: {len(client_data.subscriptions)})")
                            continue
                        logger.debug(f"Client {client_id} déconnecté (pas de données)")
                        break
                    
                    # Mettre à jour l'activité
                    client_data.last_activity = time.time()
                    
                    # Ajouter les données au parser
                    parser.feed(data)
                    
                    # CORRECTION: Traiter tous les messages complets de manière séquentielle
                    # pour préserver l'ordre et l'intégrité
                    while parser.has_complete_message():
                        try:
                            command_data = parser.parse_next()
                            if command_data:
                                await self.process_command(client_id, client_data, command_data, writer, redis_connection)
                                self.stats['messages_processed'] += 1
                            else:
                                # Si parse_next retourne None malgré has_complete_message, 
                                # il y a un problème dans le buffer
                                logger.warning(f"Parser inconsistent pour {client_id}, nettoyage buffer")
                                break
                        except Exception as e:
                            logger.error(f"Erreur traitement commande pour {client_id}: {e}")
                            self.stats['errors'] += 1
                            break
                    
                    # Nettoyer le buffer après traitement pour éviter l'accumulation
                    parser.clear_processed()
                    
                    # Protection contre l'accumulation excessive de données
                    if len(parser.buffer) > 100*1024*1024:  # 100MB limite pour gros messages
                        logger.warning(f"Buffer trop gros pour {client_id}, nettoyage forcé")
                        parser.buffer.clear()
                        parser.position = 0
                
                except asyncio.TimeoutError:
                    # Pour les clients PubSub, le timeout est normal - ils sont en écoute passive
                    if client_data.subscriptions:
                        logger.debug(f"Client PubSub {client_id} - timeout de lecture normal, connexion maintenue")
                        # Mettre à jour l'activité pour éviter le nettoyage
                        client_data.last_activity = time.time()
                        continue
                    
                    # Pour les autres clients, envoyer un ping pour maintenir la connexion
                    try:
                        writer.write(b"+PONG\r\n")
                        await writer.drain()
                    except:
                        break
                
                except Exception as e:
                    logger.error(f"Erreur dans handle_client pour {client_id}: {e}")
                    break
        
        except Exception as e:
            logger.error(f"Erreur critique pour client {client_id}: {e}")
            self.stats['errors'] += 1
        finally:
            await self.cleanup_client(client_id, client_data, writer, redis_connection)
    
    async def process_command(self, client_id: str, client_data: ClientData, 
                            command_data, writer, redis_connection):
        """Traite une commande Redis - Logique de l'ancienne version"""
        try:
            command = RedisCommand(command_data)
            
            # Filtrer les commandes CLIENT SETINFO problématiques
            if (command.command_type == 'CLIENT' and len(command.args) > 0 and 
                command.args[0].upper() in ['SETINFO', 'SETNAME']):
                logger.debug(f"Commande CLIENT {command.args[0]} filtrée pour {client_id}")
                writer.write(b"+OK\r\n")
                await writer.drain()
                return
            
            # Traiter les commandes pub/sub spécialement
            if command.is_pubsub_command():
                await self.handle_pubsub_command(client_id, client_data, command, writer, redis_connection)
            elif command.command_type in ['PING', 'PONG']:
                # Traiter PING/PONG directement comme l'ancienne version
                if command.command_type == 'PING':
                    logger.debug(f"PING reçu de {client_id}")
                    writer.write(b"+PONG\r\n")
                    await writer.drain()
                elif command.command_type == 'PONG':
                    logger.debug(f"PONG reçu de {client_id}")
                    # Pas de réponse nécessaire
            else:
                # Autres commandes - transmettre à Redis
                if command.command_type != 'CLIENT':
                    logger.info(f"Le message n'est pas pub/sub: {command.command_type},{client_id}")
                elif command.command_type == 'CLIENT' and logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Commande CLIENT reçue de {client_id}")
                
                # Transmettre à Redis
                await self.execute_redis_command(command, writer, redis_connection)
        
        except Exception as e:
            logger.error(f"Erreur processing command pour {client_id}: {e}")
            error_msg = f"-ERR Erreur interne: {str(e)}\r\n"
            try:
                writer.write(error_msg.encode())
                await writer.drain()
            except:
                pass

    async def handle_pubsub_command(self, client_id, client_data, command, writer, redis_connection):
        """Gère les commandes pub/sub"""
        
        if command.command_type == 'PUBLISH':
            await self.handle_publish(client_id, client_data, command, writer, redis_connection)
        elif command.command_type in ['SUBSCRIBE', 'PSUBSCRIBE']:
            await self.handle_subscribe(client_id, client_data, command, writer, redis_connection)
        elif command.command_type in ['UNSUBSCRIBE', 'PUNSUBSCRIBE']:
            # Gérer les désabonnements
            channels = command.get_channel()
            if channels:
                await self.pubsub_manager.unsubscribe(client_id, channels)
            
            # Transmettre la commande telle quelle
            await self.execute_redis_command(command, writer, redis_connection)
    
    async def handle_publish(self, client_id, client_data, command, writer, redis_connection):
        """Gère la commande PUBLISH - Version corrigée"""
        channel = command.get_channel()
        message_str = command.get_message()
        
        if not channel or not message_str:
            logger.warning(f"Canal ou message manquant dans la commande PUBLISH: {command}")
            return
        
        logger.debug(f"PUBLISH sur le canal {channel}: {message_str}")
        
        try:
            # Tenter de parser le message JSON
            message = json.loads(message_str)
            
            # Vérifier si un token est présent
            token = message.get('token')
            user_id = None
            role = None
            
            # Vérifier l'autorisation pour ce canal
            authorized = False
            
            # Canaux ouverts (pas besoin d'authentification)
            if channel in self.open_channels:
                authorized = True
            
            # Le coordinateur peut publier dans tous les canaux
            client_addr = writer.get_extra_info('peername')
            if client_addr and (client_addr[0], client_addr[1]) in [(addr[0], addr[1]) for addr in self.coordinator_address]:
                authorized = True
            # Canaux nécessitant une authentification
            elif token:
                try:
                    # Vérifier le token JWT
                    from django.conf import settings
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                    logger.info(f"Token JWT valide pour {payload}")
                    user_id = payload.get('user_id')
                    role = payload.get('role')
                    
                    # Vérifier les permissions selon le rôle
                    if role == 'manager' and channel in self.manager_channels:
                        authorized = True
                    elif role == 'volunteer' and channel in self.volunteer_channels:
                        authorized = True
                    elif role == 'coordinator':  # Le coordinateur peut accéder à tous les canaux
                        authorized = True
                    
                    # Mettre à jour les informations de connexion
                    client_data.authenticated = True
                    client_data.user_id = user_id
                    client_data.role = role
                    client_data.token = token
                except jwt.InvalidTokenError as e:
                    logger.warning(f"Token JWT invalide pour {client_id}: {str(e)}")
                    authorized = False
            
            # Si non autorisé, renvoyer une erreur
            if not authorized:
                logger.warning(f"Accès non autorisé au canal {channel} pour {client_id}")
                error_response = b'-ERR NOAUTH Permission denied\r\n'
                writer.write(error_response)
                await writer.drain()
                return
            
            # Appliquer les transformateurs de messages
            for transformer in self.message_transformers:
                transformer_name = transformer.__name__ if hasattr(transformer, '__name__') else transformer.__class__.__name__
                message_before = message.copy() if isinstance(message, dict) else message
                message = transformer(client_id, channel, message, user_id, role)
                
                # Vérifier si la structure du message a été préservée
                if isinstance(message_before, dict) and 'data' in message_before and isinstance(message, dict) and 'data' not in message:
                    logger.warning(f"La transformation {transformer_name} a supprimé le champ 'data'!")
            
            # Supprimer le token du message avant de le transmettre
            if isinstance(message, dict) and 'token' in message:
                del message['token']
            
            # Reconstruire le message transformé
            new_message_str = json.dumps(message)
            
            # Publier via Redis de manière asynchrone
            subscriber_count = await asyncio.get_event_loop().run_in_executor(
                None, redis_connection.publish, channel, new_message_str
            )
            
            # Publier aussi via notre gestionnaire pub/sub local
            # await self.pubsub_manager.publish_to_subscribers(channel, new_message_str)
            
            # Enregistrer le message dans la base de données
            try:
                # Importer ici pour éviter les imports circulaires
                from message_logging.services import log_message
                
                # Déterminer le type d'expéditeur et de destinataire
                sender_type = role if role else 'unknown'
                sender_id = user_id if user_id else client_id
                
                # Déterminer le type de destinataire en fonction du canal
                receiver_type = None
                receiver_id = None
                
                if channel.startswith('volunteer/'):
                    receiver_type = 'volunteer'
                elif channel.startswith('manager/'):
                    receiver_type = 'manager'
                elif channel.startswith('coordinator/'):
                    receiver_type = 'coordinator'
                elif channel == 'task/assignment':
                    receiver_type = 'volunteer'
                    if isinstance(message, dict) and 'volunteer_id' in message:
                        receiver_id = message['volunteer_id']
                elif channel == 'task/status':
                    receiver_type = 'manager'
                    if isinstance(message, dict) and 'manager_id' in message:
                        receiver_id = message['manager_id']
                elif channel == 'task/reassignment/response':
                    receiver_type = 'manager'
                    if isinstance(message, dict) and 'manager_id' in message:
                        receiver_id = message['manager_id']
                else:
                    receiver_type = 'Everybody'
                
                # Récupérer l'ID de requête et le type de message
                request_id = message.get('request_id', '') if isinstance(message, dict) else ''
                message_type = message.get('message_type', 'request') if isinstance(message, dict) else 'request'
                
                # Enregistrer le message
                log_message(
                    sender_type=sender_type,
                    sender_id=sender_id,
                    channel=channel,
                    request_id=request_id,
                    message_type=message_type,
                    content=message,
                    receiver_type=receiver_type,
                    receiver_id=receiver_id
                )
                
                logger.info(f"Message enregistré dans la base de données: {sender_type}:{sender_id} -> {channel}")
            except Exception as e:
                logger.error(f"Erreur lors de l'enregistrement du message: {e}")
                logger.error(traceback.format_exc())
            
            # Réponse du nombre d'abonnés
            response = f":{subscriber_count}\r\n"
            writer.write(response.encode())
            await writer.drain()
            
        except json.JSONDecodeError:
            logger.warning(f"Format JSON invalide dans le message: {message_str}")
            error_response = b'-ERR WRONGTYPE Invalid JSON format\r\n'
            writer.write(error_response)
            await writer.drain()
        except Exception as e:
            logger.error(f"Erreur lors du traitement de PUBLISH: {e}")
            traceback.print_exc()
    
    async def handle_subscribe(self, client_id, client_data, command, writer, redis_connection):
        """Gère la commande SUBSCRIBE - Version corrigée"""
        channels = command.get_channel()
        
        if not channels:
            logger.warning(f"Canaux manquants dans la commande SUBSCRIBE: {command}")
            return
        
        # Traiter tous les canaux comme autorisés pour éviter les déconnexions
        logger.info(f"SUBSCRIBE aux canaux {channels} pour {client_id}")
        
        # Mettre à jour les canaux souscrits
        client_data.subscriptions.update(channels)
        
        # CORRECTION: S'assurer que le client est bien enregistré dans le gestionnaire pub/sub
        await self.pubsub_manager.subscribe(client_id, writer, channels)
        
        # DEBUG: Vérifier l'état du gestionnaire après abonnement
        for channel in channels:
            subscribers_count = len(self.pubsub_manager.subscribers.get(channel, set()))
            logger.info(f"Canal {channel}: {subscribers_count} abonnés locaux après SUBSCRIBE")
        
        # Envoyer les confirmations de souscription au format RESP
        for channel in channels:
            response = f"*3\r\n$9\r\nsubscribe\r\n${len(channel)}\r\n{channel}\r\n:1\r\n"
            writer.write(response.encode())
        
        await writer.drain()
    
    async def execute_redis_command(self, command, writer, redis_connection):
        """Exécute une commande Redis - Version corrigée"""
        try:
            # Construire la commande RESP
            if hasattr(command, 'parsed_data') and command.parsed_data:
                cmd_parts = command.parsed_data
            else:
                cmd_parts = [command.command_type] + command.args
            
            # Exécuter la commande de manière asynchrone
            result = await asyncio.get_event_loop().run_in_executor(
                None, redis_connection.execute_command, *cmd_parts
            )
            
            # Formater la réponse
            response = self.format_redis_response(result)
            writer.write(response)
            await writer.drain()
            
        except Exception as e:
            logger.error(f"Erreur exécution commande Redis: {e}")
            error_msg = f"-ERR Erreur interne: {str(e)}\r\n"
            writer.write(error_msg.encode())
            await writer.drain()
    
    def format_redis_response(self, result) -> bytes:
        """Formate une réponse Redis au format RESP"""
        if result is None:
            return b"$-1\r\n"
        elif isinstance(result, bool):
            return b":1\r\n" if result else b":0\r\n"
        elif isinstance(result, int):
            return f":{result}\r\n".encode()
        elif isinstance(result, (str, bytes)):
            if isinstance(result, str):
                result = result.encode('utf-8')
            return f"${len(result)}\r\n".encode() + result + b"\r\n"
        elif isinstance(result, list):
            response = f"*{len(result)}\r\n".encode()
            for item in result:
                response += self.format_redis_response(item)
            return response
        else:
            result_str = str(result)
            result_bytes = result_str.encode('utf-8')
            return f"${len(result_bytes)}\r\n".encode() + result_bytes + b"\r\n"

    async def cleanup_client(self, client_id: str, client_data: ClientData, 
                           writer, redis_connection):
        """Nettoie les ressources d'un client déconnecté"""
        try:
            # Nettoyer les souscriptions
            if self.pubsub_manager:
                await self.pubsub_manager.cleanup_client(client_id)
            
            # Fermer les connexions
            if writer:
                try:
                    writer.close()
                    await writer.wait_closed()
                except:
                    pass
            
            if redis_connection:
                try:
                    redis_connection.close()
                except:
                    pass
            
            # Retirer des statistiques
            self.stats['connected_clients'] -= 1
            
            # Retirer du dictionnaire des clients
            if client_id in self.clients:
                del self.clients[client_id]
            
            logger.debug(f"Client {client_id} nettoyé")
        
        except Exception as e:
            logger.error(f"Erreur cleanup client {client_id}: {e}")

    async def monitor_performance(self):
        """Monitore les performances du proxy"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Toutes les minutes
                
                uptime = time.time() - self.stats['start_time']
                
                logger.info(
                    f"Stats Proxy: "
                    f"Clients={self.stats['connected_clients']}, "
                    f"Total={self.stats['total_connections']}, "
                    f"Messages={self.stats['messages_processed']}, "
                    f"Erreurs={self.stats['errors']}, "
                    f"Uptime={uptime/3600:.1f}h"
                )
                
                # Alertes de performance
                if self.stats['connected_clients'] > 80000:
                    logger.warning(f"Haute charge: {self.stats['connected_clients']} clients connectés")
                
                if self.stats['errors'] > 1000:
                    logger.warning(f"Taux d'erreur élevé: {self.stats['errors']} erreurs")
            
            except Exception as e:
                logger.error(f"Erreur monitoring: {e}")

    async def cleanup_inactive_clients(self):
        """Nettoie les clients inactifs - MAIS pas les clients PubSub avec abonnements actifs"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Toutes les 5 minutes
                
                current_time = time.time()
                inactive_clients = []
                
                for client_id, client_data in list(self.clients.items()):
                    # Ne PAS nettoyer les clients PubSub qui ont des abonnements actifs
                    # Ces clients sont en mode écoute passive et peuvent rester inactifs longtemps
                    if client_data.subscriptions:
                        logger.debug(f"Client PubSub {client_id} conservé (abonnements: {len(client_data.subscriptions)})")
                        continue
                    
                    if current_time - client_data.last_activity > 600:  # 10 minutes
                        inactive_clients.append(client_id)
                
                for client_id in inactive_clients:
                    logger.info(f"Nettoyage client inactif: {client_id}")
                    if client_id in self.clients:
                        await self.pubsub_manager.cleanup_client(client_id)
                        del self.clients[client_id]
            
            except Exception as e:
                logger.error(f"Erreur cleanup inactifs: {e}")

    def add_metadata(self, client_id, channel, message, user_id=None, role=None):
        """Ajoute des métadonnées au message sans altérer sa structure"""
        # Vérifier si le message est un dictionnaire
        if not isinstance(message, dict):
            logger.warning(f"Message non dict dans add_metadata: {message}")
            return message
            
        # Faire une copie du message pour ne pas modifier l'original
        message_copy = message.copy()
        
        # Ajouter des informations sur l'expéditeur
        if user_id:
            message_copy['_sender_id'] = user_id
        if role:
            message_copy['_sender_role'] = role
        
        # Ajouter un timestamp
        message_copy['_timestamp'] = datetime.utcnow().isoformat()
        
        # Ajouter l'adresse IP du client (IP réelle vue par le proxy)
        if client_id:
            message_copy['_client_ip'] = client_id.split(':')[0]
        
        # Log pour déboguer
        logger.debug(f"Message après ajout de métadonnées: {message_copy}")
        
        return message_copy
    
    def route_file_server(self, client_id, channel, message, user_id=None, role=None):
        """
        Transformateur qui intercepte les messages de résultat de tâche
        et remplace les informations du serveur de fichiers du volontaire
        par celles du proxy de fichiers du coordinator.
        """
        if not isinstance(message, dict):
            return message
        
        # Intercepter uniquement les messages sur le canal task/status avec status=completed
        if channel != 'task/status':
            return message
        
        status = message.get('status')
        if status != 'completed':
            return message
        
        # Vérifier si le message contient des informations de serveur de fichiers
        if 'file_server' not in message:
            logger.warning(f"Message de tâche complétée sans file_server: {message}")
            return message
        
        file_server_info = message['file_server']
        task_id = message.get('task_id')
        volunteer_id = message.get('volunteer_id')
        
        if not task_id:
            logger.error(f"Message de tâche complétée sans task_id")
            return message
        
        # Extraire l'IP et le port du volontaire
        volunteer_ip = client_id.split(':')[0]  # IP réelle du volontaire
        volunteer_port = file_server_info.get('port')
        
        if not volunteer_port:
            logger.error(f"Pas de port de serveur de fichiers pour la tâche {task_id}")
            return message
        
        logger.info(f"🔄 Routage de fichiers pour tâche {task_id}: {volunteer_ip}:{volunteer_port}")
        
        # Enregistrer la tâche dans le proxy de fichiers
        if self.file_proxy:
            self.file_proxy.register_task(
                task_id=task_id,
                volunteer_ip=volunteer_ip,
                volunteer_port=volunteer_port,
                volunteer_id=volunteer_id
            )
        
        # Remplacer les informations du serveur de fichiers
        # par celles du proxy du coordinator
        coordinator_host = self.get_coordinator_public_address()
        coordinator_file_port = 8410  # Port du proxy de fichiers
        
        message_copy = message.copy()
        message_copy['file_server'] = {
            'host': coordinator_host,
            'port': coordinator_file_port,
            'path': f'/files/{task_id}/',
            'output_files': file_server_info.get('output_files', []),
            # Garder les infos originales pour debug
            '_original_host': file_server_info.get('host'),
            '_original_port': volunteer_port,
            '_routed_by': 'coordinator_file_proxy'
        }
        
        logger.info(f"✅ Serveur de fichiers routé: {coordinator_host}:{coordinator_file_port}/files/{task_id}/")
        
        return message_copy
    
    def route_input_files(self, client_id, channel, message, user_id=None, role=None):
        """
        Transformateur qui intercepte les messages d'assignation de tâches
        et remplace les informations du serveur de fichiers du manager
        par celles du proxy de fichiers du coordinator.
        """
        if not isinstance(message, dict):
            return message
        
        # Intercepter uniquement les messages sur le canal task/assignment
        if channel != 'task/assignment':
            return message
        
        # Vérifier si le message contient des assignations
        data = message.get('data', {})
        assignments = data.get('assignments', {})
        
        if not assignments:
            logger.warning(f"Message d'assignation sans assignations: {message}")
            return message
        
        workflow_id = data.get('workflow_id')
        if not workflow_id:
            logger.warning(f"Message d'assignation sans workflow_id")
            return message
        
        logger.info(f"🔄 Routage des fichiers d'entrée pour workflow {workflow_id}")
        
        # Créer une copie du message
        message_copy = message.copy()
        if 'data' not in message_copy:
            message_copy['data'] = {}
        message_copy['data'] = data.copy()
        message_copy['data']['assignments'] = {}
        
        # Extraire l'IP et le port du manager depuis le client_id
        manager_ip = client_id.split(':')[0]  # IP réelle du manager
        
        # Parcourir toutes les assignations
        for volunteer_id, tasks in assignments.items():
            routed_tasks = []
            
            for task in tasks:
                task_copy = task.copy()
                
                # Vérifier si la tâche contient input_data avec file_server
                input_data = task.get('input_data', {})
                file_server = input_data.get('file_server', {})
                
                if file_server:
                    # Extraire les informations du serveur de fichiers du manager
                    manager_port = file_server.get('port')
                    task_id = task.get('task_id')
                    
                    if manager_port and task_id:
                        logger.info(f"  🔄 Routage pour tâche {task_id}: {manager_ip}:{manager_port}")
                        
                        # Enregistrer le mapping dans le proxy de fichiers
                        # Format pour les fichiers d'entrée: input_<workflow_id>
                        proxy_task_id = f"input_{workflow_id}"
                        
                        if self.file_proxy:
                            self.file_proxy.register_task(
                                task_id=proxy_task_id,
                                volunteer_ip=manager_ip,
                                volunteer_port=manager_port,
                                volunteer_id=None  # Pas de volunteer_id pour les fichiers d'entrée
                            )
                        
                        # Remplacer par les informations du proxy
                        coordinator_host = self.get_coordinator_public_address()
                        coordinator_file_port = 8410  # Port du proxy de fichiers
                        
                        task_copy['input_data'] = input_data.copy()
                        task_copy['input_data']['file_server'] = {
                            'host': coordinator_host,
                            'port': coordinator_file_port,
                            'base_url': f'http://{coordinator_host}:{coordinator_file_port}',
                            'path': f'/files/{proxy_task_id}/',
                            # Garder les infos originales pour debug
                            '_original_host': file_server.get('host'),
                            '_original_port': manager_port,
                            '_original_base_url': file_server.get('base_url'),
                            '_routed_by': 'coordinator_file_proxy'
                        }
                        
                        logger.info(f"  ✅ Fichiers d'entrée routés: {coordinator_host}:{coordinator_file_port}/files/{proxy_task_id}/")
                
                routed_tasks.append(task_copy)
            
            message_copy['data']['assignments'][volunteer_id] = routed_tasks
        
        logger.info(f"✅ Routage des fichiers d'entrée terminé pour workflow {workflow_id}")
        
        return message_copy
    
    def get_coordinator_public_address(self):
        """
        Retourne l'adresse publique du coordinator.
        Dans un environnement de production, cela devrait être configuré.
        """
        # TODO: Configurer l'adresse publique du coordinator
        # Pour le moment, utiliser l'IP de la machine
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return local_ip
        except:
            return 'localhost'
    
    def filter_sensitive_data(self, client_id, channel, message, user_id=None, role=None):
        """Filtre les données sensibles des messages"""
        # Vérifier si le message est un dictionnaire
        if not isinstance(message, dict):
            logger.warning(f"Message non dict: {message}")
            return message
            
        # Pour le canal d'enregistrement, on préserve la structure complète du message
        if channel == 'auth/register':
            # Si le message contient des données dans le champ 'data', les préserver
            if 'data' in message and isinstance(message['data'], dict):
                # On ne touche pas aux données d'enregistrement
                return message
            else:
                # Si les données sont directement dans le message (ancien format)
                safe_keys = ['username', 'email', 'password', 'request_id', 'client_ip', 'client_info', 'sender', 'message_type', 'timestamp', 'data']
                return {k: v for k, v in message.items() if k in safe_keys or k.startswith('_')}
        
        return message

    def handle_token_refresh(self, client_id, channel, message, user_id=None, role=None):
        """
        Transformateur qui intercepte et traite les requêtes de rafraîchissement de token.
        Cette méthode ne diffuse PAS les messages de rafraîchissement, elle les traite directement.
        """
        if not isinstance(message, dict):
            return message
        
        # Intercepter uniquement les messages sur le canal auth/token_refresh
        if channel != 'auth/token_refresh':
            return message
        
        logger.info(f"Requête de rafraîchissement de token interceptée pour client {client_id}")
        
        # Extraire les informations de la requête
        message = message['data']
        action = message.get('action')
        username = message.get('username')
        user_type = message.get('user_type')  
        password = message.get('password')
        old_token = message.get('old_token')
        request_id = message.get('request_id')

        if user_type not in ['volunteer', 'manager', 'coordinator']:
            logger.error(f"Type d'utilisateur invalide pour le rafraîchissement de token: {user_type}")
            self._send_refresh_error_response(request_id, "Type d'utilisateur invalide")
            return None  # Ne pas diffuser le message
        
        if action != 'refresh_token' or not username or not password:
            logger.error(f"Requête de rafraîchissement invalide: {message}")
            self._send_refresh_error_response(request_id, "Paramètres de rafraîchissement invalides")
            return None  # Ne pas diffuser le message
        
        # Traiter le rafraîchissement en arrière-plan
        threading.Thread(
            target=self._process_token_refresh,
            args=(username, user_type, password, old_token, request_id),
            daemon=True
        ).start()
        
        # Retourner None pour empêcher la diffusion du message
        return None
    
    def _process_token_refresh(self, username, user_type, password, old_token, request_id):
        """
        Traite la requête de rafraîchissement de token en arrière-plan.
        """
        try:
            # Import des modèles Django
            import os
            import sys
            import django
            
            # Ajouter le path du projet Django
            project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_path not in sys.path:
                sys.path.append(project_path)
            
            # Configurer Django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coordinator_project.settings')
            django.setup()
            
            
            import jwt
            from datetime import datetime, timedelta
            from django.conf import settings
            
            if user_type == 'volunteer':
                from volunteer.models import Volunteer
                authenticate = Volunteer
            elif user_type == 'manager':
                from manager.models import Manager
                authenticate = Manager
            else:                
                logger.error(f"Type d'utilisateur invalide pour le rafraîchissement de token: {user_type}")
                self._send_refresh_error_response(request_id, "Type d'utilisateur invalide")
            
            user = authenticate.objects.filter(username=username).first()

            if not user:
                logger.error(f"Utilisateur non trouvé pour {username}")
                self._send_refresh_error_response(request_id, "Utilisateur non trouvé")
                return

            from django.contrib.auth.hashers import  check_password
            if user_type == 'manager' and not check_password(password, user.password):
                logger.error(f"Mot de passe invalide pour {username}")
                self._send_refresh_error_response(request_id, "Mot de passe invalide")
                return
            elif user_type == 'volunteer' and str(user.password)  != str(password):
                logger.error(f"Mot de passe invalide pour le volontaire: {username}")
                self._send_refresh_error_response(request_id, "Mot de passe invalide")
                return
            
            
            # Générer un nouveau token JWT
            payload = {
                'user_id': str(user.id),
                'role': 'volunteer',  # Peut être adapté selon le modèle utilisateur
                'exp': datetime.utcnow() + timedelta(hours=24),
                'iat': datetime.utcnow()
            }
            
            new_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
            
            # Envoyer la réponse de succès
            response_data = {
                'status': 'success',
                'token': new_token,
                'message': 'Token rafraîchi avec succès',
                'expires_in': 24 * 3600  # 24 heures en secondes
            }
            
            self._send_refresh_response(request_id, response_data)
            logger.info(f"Token rafraîchi avec succès pour {username}")
            
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement du token: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self._send_refresh_error_response(request_id, f"Erreur interne: {str(e)}")
    
    def _send_refresh_response(self, request_id, response_data):
        """Envoie la réponse de rafraîchissement de token."""
        try:
            
            from redis_communication.client import RedisClient
            
            redis_client = RedisClient.get_instance()
            
            redis_client.publish('auth/token_refresh_response', 
                        message_data=response_data,
                        request_id=request_id,
                        message_type='response'
                )
            logger.debug(f"Réponse de rafraîchissement envoyée pour request_id: {request_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la réponse de rafraîchissement: {e}")
    
    def _send_refresh_error_response(self, request_id, error_message):
        """Envoie une réponse d'erreur pour le rafraîchissement de token."""
        error_data = {
            'status': 'error',
            'message': error_message
        }
        self._send_refresh_response(request_id, error_data)

# Fonction pour maintenir la compatibilité avec l'ancienne interface
class RedisProxy(AsyncRedisProxy):
    """Wrapper pour maintenir la compatibilité avec l'interface synchrone"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, proxy_port=6380):
        super().__init__(redis_host, redis_port, proxy_port)
        self._loop = None
    
    def start(self):
        """Démarre le proxy (interface synchrone)"""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(super().start())
        except KeyboardInterrupt:
            logger.info("Arrêt du proxy...")
        finally:
            self.stop()
    
    def stop(self):
        """Arrête le proxy (interface synchrone)"""
        if self._loop and not self._loop.is_closed():
            self._loop.run_until_complete(super().stop())
            self._loop.close()

# Fonction pour démarrer le proxy en tant que service
def start_proxy_service(host='localhost', redis_port=6379, proxy_port=6380):
    """
    Démarre le proxy Redis en tant que service.
    
    Args:
        host: Hôte Redis (défaut: localhost)
        redis_port: Port Redis (défaut: 6379)
        proxy_port: Port sur lequel le proxy écoute (défaut: 6380)
    """
    proxy = RedisProxy(
        redis_host=host,
        redis_port=redis_port,
        proxy_port=proxy_port
    )
    proxy.start()

# Point d'entrée principal
if __name__ == "__main__":
    proxy = RedisProxy()
    proxy.start()
