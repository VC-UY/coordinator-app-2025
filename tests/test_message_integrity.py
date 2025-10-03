#!/usr/bin/env python3
"""
Test d'intégrité et de latence des messages pour le proxy Redis.
Teste différentes tailles de messages avec plusieurs publishers/receivers.
"""

import asyncio
import json
import time
import hashlib
import random
import string
import statistics
import logging
from typing import Dict, List, Tuple
from collections import defaultdict
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('MessageIntegrityTest')

class MessageIntegrityTester:
    """Testeur d'intégrité des messages avec latence"""
    
    def __init__(self, proxy_host='localhost', proxy_port=6380):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.test_results = {}
        self.message_tracking = defaultdict(dict)  # message_id -> {sent_time, received_count, receivers}
        
    def generate_test_message(self, size_kb: int, message_id: str) -> str:
        """Génère un message de test avec une taille spécifique"""
        # Créer un payload de la taille demandée
        target_size = size_kb * 1024
        
        # Données de base
        base_data = {
            "message_id": message_id,
            "timestamp": time.time(),
            "sender": "test_publisher",
            "message_type": "integrity_test",
            "test_data": {
                "size_kb": size_kb,
                "sequence": list(range(100)),  # Données structurées pour vérification
                "metadata": {
                    "test_run": time.strftime("%Y%m%d_%H%M%S"),
                    "version": "1.0"
                }
            }
        }
        
        # Calculer la taille actuelle
        current_json = json.dumps(base_data)
        current_size = len(current_json.encode('utf-8'))
        
        # Ajouter du padding pour atteindre la taille cible
        if current_size < target_size:
            padding_size = target_size - current_size - 50  # Marge pour les guillemets et la clé
            padding_data = ''.join(random.choices(string.ascii_letters + string.digits, k=padding_size))
            base_data["padding"] = padding_data
        
        # Ajouter un checksum pour vérifier l'intégrité
        message_json = json.dumps(base_data, sort_keys=True)
        checksum = hashlib.sha256(message_json.encode('utf-8')).hexdigest()
        base_data["checksum"] = checksum
        
        final_message = json.dumps(base_data)
        actual_size = len(final_message.encode('utf-8')) / 1024
        
        logger.debug(f"Message généré: ID={message_id}, Taille cible={size_kb}KB, Taille réelle={actual_size:.1f}KB")
        
        return final_message
    
    def verify_message_integrity(self, received_message: str, expected_message_id: str) -> Tuple[bool, Dict]:
        """Vérifie l'intégrité d'un message reçu"""
        try:
            data = json.loads(received_message)
            
            # Vérifier l'ID du message
            if data.get("message_id") != expected_message_id:
                return False, {"error": "Message ID mismatch"}
            
            # Extraire et vérifier le checksum
            received_checksum = data.pop("checksum", None)
            if not received_checksum:
                return False, {"error": "Missing checksum"}
            
            # Recalculer le checksum
            data_without_checksum = json.dumps(data, sort_keys=True)
            calculated_checksum = hashlib.sha256(data_without_checksum.encode('utf-8')).hexdigest()
            
            if received_checksum != calculated_checksum:
                return False, {"error": "Checksum mismatch", "expected": calculated_checksum, "received": received_checksum}
            
            # Vérifier les données structurées
            test_data = data.get("test_data", {})
            sequence = test_data.get("sequence", [])
            if sequence != list(range(100)):
                return False, {"error": "Sequence data corrupted"}
            
            return True, {
                "message_id": data["message_id"],
                "size_kb": test_data.get("size_kb", 0),
                "timestamp": data.get("timestamp", 0),
                "sender": data.get("sender", "unknown")
            }
            
        except json.JSONDecodeError as e:
            return False, {"error": f"JSON decode error: {e}"}
        except Exception as e:
            return False, {"error": f"Verification error: {e}"}
    
    async def create_publisher(self, publisher_id: str, channel: str, message_sizes: List[int], messages_per_size: int):
        """Crée un publisher qui envoie des messages de différentes tailles"""
        try:
            reader, writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)
            
            sent_messages = []
            
            for size_kb in message_sizes:
                for i in range(messages_per_size):
                    message_id = f"pub_{publisher_id}_size_{size_kb}kb_msg_{i}"
                    
                    # Générer le message
                    message_content = self.generate_test_message(size_kb, message_id)
                    
                    # Enregistrer le temps d'envoi
                    send_time = time.time()
                    self.message_tracking[message_id]["sent_time"] = send_time
                    self.message_tracking[message_id]["size_kb"] = size_kb
                    self.message_tracking[message_id]["publisher_id"] = publisher_id
                    
                    # Construire la commande PUBLISH
                    publish_cmd = f"*3\r\n$7\r\nPUBLISH\r\n${len(channel)}\r\n{channel}\r\n${len(message_content)}\r\n{message_content}\r\n"
                    
                    # Envoyer le message
                    writer.write(publish_cmd.encode())
                    await writer.drain()
                    
                    # Lire la réponse
                    response = await reader.read(1024)
                    
                    sent_messages.append({
                        "message_id": message_id,
                        "size_kb": size_kb,
                        "send_time": send_time
                    })
                    
                    logger.debug(f"Publisher {publisher_id} envoyé: {message_id} ({size_kb}KB)")
                    
                    # Pause entre les messages pour éviter l'overload
                    await asyncio.sleep(0.1)
            
            writer.close()
            await writer.wait_closed()
            
            logger.info(f"Publisher {publisher_id} terminé: {len(sent_messages)} messages envoyés")
            return sent_messages
            
        except Exception as e:
            logger.error(f"Erreur dans publisher {publisher_id}: {e}")
            return []
    
    async def create_receiver(self, receiver_id: str, channel: str, expected_message_count: int, timeout: int = 30):
        """Crée un receiver qui écoute et vérifie les messages"""
        try:
            reader, writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)
            
            # S'abonner au canal
            subscribe_cmd = f"*2\r\n$9\r\nSUBSCRIBE\r\n${len(channel)}\r\n{channel}\r\n"
            writer.write(subscribe_cmd.encode())
            await writer.drain()
            
            # Lire la confirmation d'abonnement
            await reader.read(1024)
            
            received_messages = []
            start_time = time.time()
            
            logger.info(f"Receiver {receiver_id} en attente de {expected_message_count} messages...")
            
            while len(received_messages) < expected_message_count:
                if time.time() - start_time > timeout:
                    logger.warning(f"Timeout pour receiver {receiver_id}: {len(received_messages)}/{expected_message_count} reçus")
                    break
                
                try:
                    # Lire le message pub/sub
                    data = await asyncio.wait_for(reader.read(64*1024), timeout=1.0)  # 64KB buffer pour gros messages
                    
                    if not data:
                        continue
                    
                    # Parser le message RESP
                    message_content = self.parse_pubsub_message(data)
                    if not message_content:
                        continue
                    
                    receive_time = time.time()
                    
                    # Extraire l'ID du message pour vérification
                    try:
                        temp_data = json.loads(message_content)
                        message_id = temp_data.get("message_id", "unknown")
                    except:
                        message_id = "parse_error"
                    
                    # Vérifier l'intégrité
                    is_valid, verification_result = self.verify_message_integrity(message_content, message_id)
                    
                    if is_valid:
                        # Calculer la latence
                        sent_time = self.message_tracking.get(message_id, {}).get("sent_time", receive_time)
                        latency_ms = (receive_time - sent_time) * 1000
                        
                        # Enregistrer la réception
                        if "receivers" not in self.message_tracking[message_id]:
                            self.message_tracking[message_id]["receivers"] = []
                        
                        self.message_tracking[message_id]["receivers"].append({
                            "receiver_id": receiver_id,
                            "receive_time": receive_time,
                            "latency_ms": latency_ms
                        })
                        
                        received_messages.append({
                            "message_id": message_id,
                            "receiver_id": receiver_id,
                            "receive_time": receive_time,
                            "latency_ms": latency_ms,
                            "size_kb": verification_result.get("size_kb", 0),
                            "is_valid": True
                        })
                        
                        logger.debug(f"Receiver {receiver_id} reçu valide: {message_id} (latence: {latency_ms:.1f}ms)")
                    else:
                        received_messages.append({
                            "message_id": message_id,
                            "receiver_id": receiver_id,
                            "receive_time": receive_time,
                            "is_valid": False,
                            "error": verification_result.get("error", "Unknown error")
                        })
                        logger.error(f"Receiver {receiver_id} message corrompu: {message_id} - {verification_result}")
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Erreur lecture message receiver {receiver_id}: {e}")
                    continue
            
            writer.close()
            await writer.wait_closed()
            
            logger.info(f"Receiver {receiver_id} terminé: {len(received_messages)} messages reçus")
            return received_messages
            
        except Exception as e:
            logger.error(f"Erreur dans receiver {receiver_id}: {e}")
            return []
    
    def parse_pubsub_message(self, data: bytes) -> str:
        """Parse un message pub/sub RESP et extrait le contenu"""
        try:
            data_str = data.decode('utf-8', errors='replace')
            
            # Format RESP: *3\r\nmessage\r\n$channel_len\r\nchannel\r\n$content_len\r\ncontent\r\n
            lines = data_str.split('\r\n')
            
            # Trouver le contenu du message
            for i, line in enumerate(lines):
                if line == 'message' and i + 4 < len(lines):
                    # Le contenu est 4 lignes plus loin
                    if i + 4 < len(lines):
                        content = lines[i + 4]
                        return content
            
            # Fallback: chercher du JSON dans les données
            for line in lines:
                if line.startswith('{') and line.endswith('}'):
                    return line
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur parsing message RESP: {e}")
            return None
    
    async def run_message_integrity_test(self, test_config: Dict):
        """Lance un test d'intégrité des messages"""
        print(f"\n🧪 Test d'intégrité: {test_config['name']}")
        print("=" * 50)
        
        channel = test_config['channel']
        publishers_count = test_config['publishers']
        receivers_count = test_config['receivers']
        message_sizes = test_config['message_sizes']  # en KB
        messages_per_size = test_config['messages_per_size']
        
        total_messages = publishers_count * len(message_sizes) * messages_per_size
        
        print(f"📊 Configuration:")
        print(f"  Publishers: {publishers_count}")
        print(f"  Receivers: {receivers_count}")
        print(f"  Tailles de messages: {message_sizes} KB")
        print(f"  Messages par taille: {messages_per_size}")
        print(f"  Total messages attendus: {total_messages}")
        
        # Réinitialiser le tracking
        self.message_tracking.clear()
        
        # Démarrer les receivers en premier
        receiver_tasks = []
        for i in range(receivers_count):
            task = asyncio.create_task(
                self.create_receiver(f"recv_{i}", channel, total_messages, timeout=60)
            )
            receiver_tasks.append(task)
        
        # Attendre un peu pour que les receivers s'abonnent
        await asyncio.sleep(1)
        
        # Démarrer les publishers
        publisher_tasks = []
        for i in range(publishers_count):
            task = asyncio.create_task(
                self.create_publisher(f"pub_{i}", channel, message_sizes, messages_per_size)
            )
            publisher_tasks.append(task)
        
        # Attendre que tous les publishers terminent
        publisher_results = await asyncio.gather(*publisher_tasks, return_exceptions=True)
        
        # Attendre un peu plus pour que tous les messages soient reçus
        await asyncio.sleep(5)
        
        # Arrêter les receivers
        for task in receiver_tasks:
            task.cancel()
        
        receiver_results = await asyncio.gather(*receiver_tasks, return_exceptions=True)
        
        # Analyser les résultats
        return self.analyze_results(test_config, publisher_results, receiver_results)
    
    def analyze_results(self, test_config: Dict, publisher_results: List, receiver_results: List) -> Dict:
        """Analyse les résultats du test"""
        analysis = {
            "test_name": test_config['name'],
            "config": test_config,
            "summary": {},
            "latency_stats": {},
            "integrity_stats": {},
            "size_analysis": {}
        }
        
        # Compter les messages envoyés
        total_sent = 0
        for result in publisher_results:
            if isinstance(result, list):
                total_sent += len(result)
        
        # Compter les messages reçus et analyser
        total_received = 0
        valid_messages = 0
        corrupted_messages = 0
        latencies_by_size = defaultdict(list)
        reception_count_per_message = defaultdict(int)
        
        for result in receiver_results:
            if isinstance(result, list):
                for msg in result:
                    total_received += 1
                    if msg.get("is_valid", False):
                        valid_messages += 1
                        latency = msg.get("latency_ms", 0)
                        size_kb = msg.get("size_kb", 0)
                        latencies_by_size[size_kb].append(latency)
                        reception_count_per_message[msg["message_id"]] += 1
                    else:
                        corrupted_messages += 1
        
        # Statistiques générales
        expected_total_receptions = total_sent * test_config['receivers']
        delivery_rate = (total_received / expected_total_receptions * 100) if expected_total_receptions > 0 else 0
        integrity_rate = (valid_messages / total_received * 100) if total_received > 0 else 0
        
        analysis["summary"] = {
            "messages_sent": total_sent,
            "total_receptions": total_received,
            "expected_receptions": expected_total_receptions,
            "valid_messages": valid_messages,
            "corrupted_messages": corrupted_messages,
            "delivery_rate_percent": delivery_rate,
            "integrity_rate_percent": integrity_rate
        }
        
        # Statistiques de latence par taille
        for size_kb, latencies in latencies_by_size.items():
            if latencies:
                analysis["latency_stats"][f"{size_kb}KB"] = {
                    "count": len(latencies),
                    "min_ms": min(latencies),
                    "max_ms": max(latencies),
                    "avg_ms": statistics.mean(latencies),
                    "median_ms": statistics.median(latencies),
                    "p99_ms": sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 10 else max(latencies)
                }
        
        # Vérifier la duplication/perte de messages
        duplicate_messages = 0
        lost_messages = 0
        perfect_delivery = 0
        
        for message_id, count in reception_count_per_message.items():
            expected_count = test_config['receivers']
            if count == expected_count:
                perfect_delivery += 1
            elif count > expected_count:
                duplicate_messages += count - expected_count
            elif count < expected_count:
                lost_messages += expected_count - count
        
        analysis["integrity_stats"] = {
            "perfect_delivery_messages": perfect_delivery,
            "messages_with_duplicates": sum(1 for count in reception_count_per_message.values() if count > test_config['receivers']),
            "messages_with_losses": sum(1 for count in reception_count_per_message.values() if count < test_config['receivers']),
            "total_duplicates": duplicate_messages,
            "total_losses": lost_messages
        }
        
        return analysis
    
    def print_analysis(self, analysis: Dict):
        """Affiche l'analyse des résultats"""
        print(f"\n📊 RÉSULTATS - {analysis['test_name']}")
        print("=" * 60)
        
        summary = analysis["summary"]
        print(f"📤 Messages envoyés: {summary['messages_sent']:,}")
        print(f"📥 Réceptions totales: {summary['total_receptions']:,}")
        print(f"📋 Réceptions attendues: {summary['expected_receptions']:,}")
        print(f"✅ Messages valides: {summary['valid_messages']:,}")
        print(f"❌ Messages corrompus: {summary['corrupted_messages']:,}")
        print(f"📈 Taux de livraison: {summary['delivery_rate_percent']:.1f}%")
        print(f"🛡️ Taux d'intégrité: {summary['integrity_rate_percent']:.1f}%")
        
        print(f"\n⏱️ LATENCES PAR TAILLE:")
        for size, stats in analysis["latency_stats"].items():
            print(f"  {size}: avg={stats['avg_ms']:.1f}ms, p99={stats['p99_ms']:.1f}ms, max={stats['max_ms']:.1f}ms")
        
        integrity = analysis["integrity_stats"]
        print(f"\n🎯 INTÉGRITÉ DES LIVRAISONS:")
        print(f"  Livraisons parfaites: {integrity['perfect_delivery_messages']:,}")
        print(f"  Messages dupliqués: {integrity['total_duplicates']:,}")
        print(f"  Messages perdus: {integrity['total_losses']:,}")

async def main():
    """Fonction principale pour lancer les tests d'intégrité"""
    print("🚀 TESTS D'INTÉGRITÉ ET LATENCE DES MESSAGES")
    print("=" * 50)
    
    tester = MessageIntegrityTester()
    
    # Configuration des tests
    test_configs = [
        {
            "name": "Test Small Messages (1KB-10KB)",
            "channel": "test/integrity/small",
            "publishers": 3,
            "receivers": 5,
            "message_sizes": [1, 5, 10],  # KB
            "messages_per_size": 5
        },
        {
            "name": "Test Medium Messages (50KB-100KB)",
            "channel": "test/integrity/medium", 
            "publishers": 2,
            "receivers": 4,
            "message_sizes": [50, 100],  # KB
            "messages_per_size": 3
        },
        {
            "name": "Test Large Messages (500KB-1MB)",
            "channel": "test/integrity/large",
            "publishers": 2,
            "receivers": 3,
            "message_sizes": [500, 1000],  # KB  
            "messages_per_size": 2
        },
        {
            "name": "Test Mixed Load",
            "channel": "test/integrity/mixed",
            "publishers": 5,
            "receivers": 8,
            "message_sizes": [1, 10, 50, 100, 500],  # KB
            "messages_per_size": 2
        }
    ]
    
    all_results = []
    
    for config in test_configs:
        try:
            result = await tester.run_message_integrity_test(config)
            all_results.append(result)
            tester.print_analysis(result)
            
            # Pause entre les tests
            await asyncio.sleep(3)
            
        except Exception as e:
            logger.error(f"Erreur dans le test {config['name']}: {e}")
    
    # Résumé global
    print(f"\n🏆 RÉSUMÉ GLOBAL")
    print("=" * 30)
    
    total_sent = sum(r["summary"]["messages_sent"] for r in all_results)
    total_received = sum(r["summary"]["total_receptions"] for r in all_results)
    total_valid = sum(r["summary"]["valid_messages"] for r in all_results)
    
    print(f"📊 Total messages envoyés: {total_sent:,}")
    print(f"📊 Total réceptions: {total_received:,}")
    print(f"📊 Total messages valides: {total_valid:,}")
    print(f"📊 Taux d'intégrité global: {(total_valid/total_received*100):.1f}%")
    
    # Sauvegarder les résultats
    timestamp = int(time.time())
    with open(f"/tmp/integrity_test_results_{timestamp}.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n💾 Résultats sauvegardés: /tmp/integrity_test_results_{timestamp}.json")

if __name__ == "__main__":
    asyncio.run(main())