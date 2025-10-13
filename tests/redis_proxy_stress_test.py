#!/usr/bin/env python3
"""
Script de test de stress pour proxy Redis pub/sub
Compatible avec un proxy qui attend des messages au format JSON
Teste le nombre de connexions simultanées et la taille maximale des messages
"""

import redis
import threading
import time
import hashlib
import random
import string
import json
from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import defaultdict
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestConfig:
    """Configuration du test"""
    proxy_host: str = "localhost"
    proxy_port: int = 6380
    num_subscribers: int = 50
    num_publishers: int = 5
    messages_per_publisher: int = 10
    channel_name: str = "test/channel"
    initial_message_size: int = 100  # octets
    max_message_size: int = 50 * 1024 * 1024  # 50 MB
    connection_timeout: int = 10
    test_max_connections: bool = True
    test_message_sizes: bool = True
    redis_password: Optional[str] = None
    redis_db: int = 0


class MessageGenerator:
    """Génère des messages JSON avec checksum pour vérification"""
    
    @staticmethod
    def generate_message(size: int, msg_id: int) -> tuple[str, str]:
        """
        Génère un message JSON de taille spécifique avec un checksum
        Retourne (message_json, checksum)
        """
        # Créer un payload avec un ID et du contenu aléatoire
        # Format JSON compatible avec votre proxy
        
        # Calculer la taille du contenu nécessaire
        base_structure_size = 200  # Taille approximative de la structure JSON
        remaining_size = max(10, size - base_structure_size)
        
        # Générer du contenu aléatoire pour remplir
        payload = ''.join(random.choices(string.ascii_letters + string.digits, k=remaining_size))
        
        # Créer le message sans checksum d'abord
        message_data = {
            "msg_id": msg_id,
            "size": size,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload,
            "sender": "stress_test",
            "message_type": "test"
        }
        
        # Calculer le checksum du payload
        checksum = hashlib.md5(json.dumps(message_data, sort_keys=True).encode()).hexdigest()
        
        # Ajouter le checksum au message
        message_data["checksum"] = checksum
        
        # Convertir en JSON
        message_json = json.dumps(message_data)
        
        return message_json, checksum
    
    @staticmethod
    def verify_message(message_str: str) -> tuple[bool, float, str]:
        """
        Vérifie l'intégrité d'un message JSON
        Retourne (valide, pourcentage_correspondance, msg_id)
        """
        try:
            # Parser le JSON
            message = json.loads(message_str)
            
            # Extraire l'ID du message
            msg_id = str(message.get('msg_id', 'UNKNOWN'))
            
            # Extraire le checksum
            if 'checksum' not in message:
                logger.debug(f"Message sans checksum: {message_str[:100]}")
                return False, 0.0, msg_id
            
            received_checksum = message['checksum']
            
            # Retirer le checksum et recalculer
            message_copy = message.copy()
            del message_copy['checksum']
            
            # Calculer le checksum attendu
            expected_checksum = hashlib.md5(json.dumps(message_copy, sort_keys=True).encode()).hexdigest()
            
            # Comparer
            if received_checksum == expected_checksum:
                return True, 100.0, msg_id
            
            # Calculer le pourcentage de caractères correspondants
            min_len = min(len(received_checksum), len(expected_checksum))
            matches = sum(1 for i in range(min_len) if received_checksum[i] == expected_checksum[i])
            percentage = (matches / len(expected_checksum)) * 100
            
            logger.debug(f"Checksum mismatch: attendu={expected_checksum}, reçu={received_checksum}")
            
            return False, percentage, msg_id
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON: {e}")
            return False, 0.0, "UNKNOWN"
        except Exception as e:
            logger.error(f"Erreur de vérification: {e}")
            return False, 0.0, "UNKNOWN"


class TestStatistics:
    """Collecte et affiche les statistiques de test"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.messages_sent = 0
        self.messages_received = 0
        self.messages_verified = 0
        self.messages_corrupted = 0
        self.connections_succeeded = 0
        self.connections_failed = 0
        self.corruption_percentages: List[float] = []
        self.message_sizes_tested: Dict[int, bool] = {}
        self.max_working_size = 0
        self.max_connections = 0
        self.errors: List[str] = []
        self.start_time = None
        self.end_time = None
        self.corrupted_messages: List[str] = []
    
    def record_sent(self):
        with self.lock:
            self.messages_sent += 1
    
    def record_received(self):
        with self.lock:
            self.messages_received += 1
    
    def record_verified(self, percentage: float, msg_id: str = "UNKNOWN"):
        with self.lock:
            if percentage == 100.0:
                self.messages_verified += 1
            else:
                self.messages_corrupted += 1
                self.corruption_percentages.append(percentage)
                self.corrupted_messages.append(f"MSG_ID:{msg_id} - {percentage:.2f}%")
    
    def record_connection(self, success: bool):
        with self.lock:
            if success:
                self.connections_succeeded += 1
                self.max_connections = max(self.max_connections, self.connections_succeeded)
            else:
                self.connections_failed += 1
    
    def record_message_size_test(self, size: int, success: bool):
        with self.lock:
            self.message_sizes_tested[size] = success
            if success:
                self.max_working_size = max(self.max_working_size, size)
    
    def record_error(self, error: str):
        with self.lock:
            self.errors.append(error)
    
    def print_report(self):
        """Affiche le rapport complet des tests"""
        print("\n" + "="*80)
        print("RAPPORT DE TEST DU PROXY REDIS PUB/SUB")
        print("="*80)
        
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            print(f"\n⏱️  Durée du test: {duration:.2f} secondes")
        
        print("\n📊 STATISTIQUES DE CONNEXION:")
        print(f"  ✅ Connexions réussies: {self.connections_succeeded}")
        print(f"  ❌ Connexions échouées: {self.connections_failed}")
        print(f"  🔝 Connexions simultanées max: {self.max_connections}")
        
        print("\n📨 STATISTIQUES DE MESSAGES:")
        print(f"  📤 Messages envoyés: {self.messages_sent}")
        print(f"  📥 Messages reçus: {self.messages_received}")
        print(f"  ✅ Messages vérifiés (100%): {self.messages_verified}")
        print(f"  ⚠️  Messages corrompus: {self.messages_corrupted}")
        
        if self.messages_received > 0:
            success_rate = (self.messages_verified / self.messages_received) * 100
            print(f"  📈 Taux de réussite: {success_rate:.2f}%")
        
        if self.corruption_percentages:
            avg_corruption = sum(self.corruption_percentages) / len(self.corruption_percentages)
            print(f"  📉 Pourcentage moyen de correspondance (messages corrompus): {avg_corruption:.2f}%")
            
            if len(self.corrupted_messages) <= 20:
                print(f"\n  ⚠️  Détails des messages corrompus:")
                for msg in self.corrupted_messages:
                    print(f"    - {msg}")
        
        print("\n📏 TESTS DE TAILLE DE MESSAGE:")
        if self.message_sizes_tested:
            for size in sorted(self.message_sizes_tested.keys()):
                status = "✅" if self.message_sizes_tested[size] else "❌"
                size_kb = size / 1024
                if size_kb < 1024:
                    print(f"  {status} {size_kb:.2f} KB")
                else:
                    print(f"  {status} {size_kb/1024:.2f} MB")
            
            if self.max_working_size > 0:
                size_kb = self.max_working_size / 1024
                if size_kb < 1024:
                    print(f"\n  🏆 Taille maximale fonctionnelle: {size_kb:.2f} KB")
                else:
                    print(f"\n  🏆 Taille maximale fonctionnelle: {size_kb/1024:.2f} MB")
        
        if self.errors:
            print(f"\n❌ ERREURS RENCONTRÉES ({len(self.errors)}):")
            for i, error in enumerate(self.errors[:10], 1):
                print(f"  {i}. {error}")
            if len(self.errors) > 10:
                print(f"  ... et {len(self.errors) - 10} autres erreurs")
        
        print("\n" + "="*80)


class SubscriberThread(threading.Thread):
    """Thread subscriber qui écoute les messages"""
    
    def __init__(self, config: TestConfig, stats: TestStatistics, thread_id: int):
        super().__init__(name=f"Subscriber-{thread_id}")
        self.config = config
        self.stats = stats
        self.thread_id = thread_id
        self.redis_client = None
        self.pubsub = None
        self.running = True
    
    def run(self):
        """Lance le subscriber"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.proxy_host,
                port=self.config.proxy_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                socket_timeout=self.config.connection_timeout,
                socket_connect_timeout=self.config.connection_timeout,
                decode_responses=True
            )
            
            self.redis_client.ping()
            self.stats.record_connection(True)
            logger.info(f"{self.name}: Connecté et souscription au canal '{self.config.channel_name}'")
            
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe(self.config.channel_name)
            
            for message in self.pubsub.listen():
                if not self.running:
                    break
                
                if message['type'] == 'message':
                    self.stats.record_received()
                    message_data = message['data']
                    
                    # Vérifier l'intégrité
                    is_valid, percentage, msg_id = MessageGenerator.verify_message(message_data)
                    self.stats.record_verified(percentage, msg_id)
                    
                    if is_valid:
                        logger.debug(f"{self.name}: Message {msg_id} valide reçu")
                    else:
                        logger.warning(f"{self.name}: Message {msg_id} corrompu! Correspondance: {percentage:.2f}%")
                
        except redis.ConnectionError as e:
            self.stats.record_connection(False)
            error_msg = f"{self.name}: Erreur de connexion - {str(e)}"
            logger.error(error_msg)
            self.stats.record_error(error_msg)
        except Exception as e:
            error_msg = f"{self.name}: Erreur - {str(e)}"
            logger.error(error_msg)
            self.stats.record_error(error_msg)
        finally:
            if self.pubsub:
                try:
                    self.pubsub.unsubscribe()
                    self.pubsub.close()
                except:
                    pass
            if self.redis_client:
                try:
                    self.redis_client.close()
                except:
                    pass
    
    def stop(self):
        """Arrête le subscriber"""
        self.running = False


class PublisherThread(threading.Thread):
    """Thread publisher qui envoie des messages JSON"""
    
    def __init__(self, config: TestConfig, stats: TestStatistics, thread_id: int, message_size: int):
        super().__init__(name=f"Publisher-{thread_id}")
        self.config = config
        self.stats = stats
        self.thread_id = thread_id
        self.message_size = message_size
        self.redis_client = None
    
    def run(self):
        """Lance le publisher"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.proxy_host,
                port=self.config.proxy_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                socket_timeout=self.config.connection_timeout,
                socket_connect_timeout=self.config.connection_timeout,
                decode_responses=True
            )
            
            self.redis_client.ping()
            self.stats.record_connection(True)
            logger.info(f"{self.name}: Connecté, envoi de {self.config.messages_per_publisher} messages")
            
            for i in range(self.config.messages_per_publisher):
                msg_id = self.thread_id * 10000 + i
                message, checksum = MessageGenerator.generate_message(self.message_size, msg_id)
                
                try:
                    num_subscribers = self.redis_client.publish(self.config.channel_name, message)
                    self.stats.record_sent()
                    logger.debug(f"{self.name}: Message {msg_id} envoyé à {num_subscribers} subscribers (checksum: {checksum[:8]}...)")
                except Exception as e:
                    error_msg = f"{self.name}: Échec d'envoi du message {msg_id} - {str(e)}"
                    logger.error(error_msg)
                    self.stats.record_error(error_msg)
                
                time.sleep(0.1)
                
        except redis.ConnectionError as e:
            self.stats.record_connection(False)
            error_msg = f"{self.name}: Erreur de connexion - {str(e)}"
            logger.error(error_msg)
            self.stats.record_error(error_msg)
        except Exception as e:
            error_msg = f"{self.name}: Erreur - {str(e)}"
            logger.error(error_msg)
            self.stats.record_error(error_msg)
        finally:
            if self.redis_client:
                try:
                    self.redis_client.close()
                except:
                    pass


class ProxyStressTester:
    """Orchestrateur principal des tests"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.stats = TestStatistics()
    
    def test_connection(self) -> bool:
        """Teste la connexion au proxy avant de lancer les tests"""
        logger.info("Test de connexion au proxy...")
        try:
            client = redis.Redis(
                host=self.config.proxy_host,
                port=self.config.proxy_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                socket_timeout=self.config.connection_timeout,
                socket_connect_timeout=self.config.connection_timeout
            )
            client.ping()
            client.close()
            logger.info("✅ Connexion au proxy réussie!")
            return True
        except Exception as e:
            logger.error(f"❌ Impossible de se connecter au proxy: {e}")
            return False
    
    def test_concurrent_connections(self):
        """Test du nombre de connexions simultanées"""
        logger.info(f"\n{'='*80}")
        logger.info("TEST 1: Connexions simultanées avec pub/sub")
        logger.info(f"{'='*80}")
        
        self.stats.start_time = time.time()
        
        subscribers: List[SubscriberThread] = []
        publishers: List[PublisherThread] = []
        
        logger.info(f"Démarrage de {self.config.num_subscribers} subscribers...")
        for i in range(self.config.num_subscribers):
            sub = SubscriberThread(self.config, self.stats, i)
            subscribers.append(sub)
            sub.start()
            time.sleep(0.1)
        
        logger.info("Attente que tous les subscribers soient connectés...")
        time.sleep(3)
        
        logger.info(f"Démarrage de {self.config.num_publishers} publishers...")
        for i in range(self.config.num_publishers):
            pub = PublisherThread(self.config, self.stats, i, self.config.initial_message_size)
            publishers.append(pub)
            pub.start()
            time.sleep(0.1)
        
        logger.info("Attente de la fin de publication...")
        for pub in publishers:
            pub.join()
        
        logger.info("Tous les publishers ont terminé. Attente de réception des messages...")
        time.sleep(5)
        
        logger.info("Arrêt des subscribers...")
        for sub in subscribers:
            sub.stop()
        
        for sub in subscribers:
            sub.join(timeout=3)
        
        self.stats.end_time = time.time()
        
        logger.info("Test de connexions simultanées terminé!")
    
    def test_message_sizes(self):
        """Test de différentes tailles de messages"""
        if not self.config.test_message_sizes:
            return
        
        logger.info(f"\n{'='*80}")
        logger.info("TEST 2: Tailles de messages")
        logger.info(f"{'='*80}")
        
        test_sizes = [
            1024,              # 1 KB
            10 * 1024,         # 10 KB
            100 * 1024,        # 100 KB
            # 512 * 1024,        # 512 KB
            # 1024 * 1024,       # 1 MB
            # 2 * 1024 * 1024,   # 2 MB
            # 5 * 1024 * 1024,   # 5 MB
            # 10 * 1024 * 1024,  # 10 MB
            # 20 * 1024 * 1024,  # 20 MB 
            # 40 * 1024 * 1024,  # 40 MB 
            # 50 * 1024 * 1024   # 50 MB (maximum pour le proxy)
        ]
        
        for size in test_sizes:
            if size > self.config.max_message_size:
                break
            
            size_kb = size / 1024
            if size_kb < 1024:
                logger.info(f"Test avec des messages de {size_kb:.2f} KB...")
            else:
                logger.info(f"Test avec des messages de {size_kb/1024:.2f} MB...")
            
            temp_stats = TestStatistics()
            temp_stats.start_time = time.time()
            
            subscriber = SubscriberThread(self.config, temp_stats, 9999)
            subscriber.start()
            time.sleep(2)
            
            temp_config = TestConfig(
                proxy_host=self.config.proxy_host,
                proxy_port=self.config.proxy_port,
                redis_password=self.config.redis_password,
                redis_db=self.config.redis_db,
                messages_per_publisher=3,
                connection_timeout=self.config.connection_timeout
            )
            
            publisher = PublisherThread(temp_config, temp_stats, 9999, size)
            publisher.start()
            publisher.join()
            
            time.sleep(3)
            
            subscriber.stop()
            subscriber.join(timeout=3)
            
            success = (temp_stats.messages_sent > 0 and 
                      temp_stats.messages_verified > 0 and
                      temp_stats.messages_corrupted == 0)
            
            self.stats.record_message_size_test(size, success)
            
            if success:
                if size_kb < 1024:
                    logger.info(f"✅ Taille {size_kb:.2f} KB: RÉUSSI ({temp_stats.messages_verified}/{temp_stats.messages_received} messages)")
                else:
                    logger.info(f"✅ Taille {size_kb/1024:.2f} MB: RÉUSSI ({temp_stats.messages_verified}/{temp_stats.messages_received} messages)")
            else:
                if size_kb < 1024:
                    logger.warning(f"❌ Taille {size_kb:.2f} KB: ÉCHOUÉ (envoyés={temp_stats.messages_sent}, reçus={temp_stats.messages_received}, corrompus={temp_stats.messages_corrupted})")
                else:
                    logger.warning(f"❌ Taille {size_kb/1024:.2f} MB: ÉCHOUÉ (envoyés={temp_stats.messages_sent}, reçus={temp_stats.messages_received}, corrompus={temp_stats.messages_corrupted})")
                break
            
            time.sleep(1)
    
    def run_all_tests(self):
        """Lance tous les tests"""
        logger.info("Démarrage des tests du proxy Redis pub/sub")
        logger.info(f"Cible: {self.config.proxy_host}:{self.config.proxy_port}")
        
        if not self.test_connection():
            logger.error("Impossible de continuer sans connexion au proxy")
            return
        
        if self.config.test_max_connections:
            self.test_concurrent_connections()
        
        if self.config.test_message_sizes:
            self.test_message_sizes()
        
        self.stats.print_report()


def main():
    """Point d'entrée principal"""
    config = TestConfig(
        proxy_host="localhost",
        proxy_port=6380,           # Port de votre proxy
        num_subscribers=1000,
        num_publishers=30,
        messages_per_publisher=15,
        channel_name="test/channel",  # Canal ouvert dans votre proxy
        initial_message_size=1024,
        max_message_size=100 * 1024 * 1024,  # 100 MB (maximum pour le proxy)
        connection_timeout=100,
        test_max_connections=True,
        test_message_sizes=True,
        redis_password=None,
        redis_db=0
    )
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║     TEST DE STRESS POUR PROXY REDIS PUB/SUB                  ║
║                                                              ║
║  Format JSON compatible avec votre proxy                     ║
║                                                              ║
║  Ce script va tester:                                        ║
║  • Le nombre maximum de connexions simultanées               ║
║  • La taille maximale des messages supportés                 ║
║  • L'intégrité des messages (vérification par checksum)      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚙️  CONFIGURATION DU TEST:")
    print(f"  Serveur: {config.proxy_host}:{config.proxy_port}")
    print(f"  Subscribers: {config.num_subscribers}")
    print(f"  Publishers: {config.num_publishers}")
    print(f"  Messages par publisher: {config.messages_per_publisher}")
    print(f"  Canal: {config.channel_name}")
    print(f"  Taille initiale message: {config.initial_message_size / 1024:.2f} KB")
    print(f"  Taille max à tester: {config.max_message_size / (1024*1024):.2f} MB")
    
    input("\nAppuyez sur Entrée pour démarrer les tests...")
    
    tester = ProxyStressTester(config)
    tester.run_all_tests()
    
    print("\n✅ Tous les tests sont terminés!")


if __name__ == "__main__":
    main()