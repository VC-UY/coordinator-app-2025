#!/usr/bin/env python3
"""
Test d'intégrité et de latence des messages pour le proxy Redis.
Teste différentes tailles de messages avec plusieurs publishers/receivers.
Améliorations : indépendance des subscribers (vérif. 100% réception par chacun),
vérification avec % de correspondance, logs structurés par objectif.
"""

import asyncio
import json
import time
import hashlib
import random
import string
import statistics
import logging
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import difflib  # Pour % de correspondance

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MessageIntegrityTest')

class MessageIntegrityTester:
    """Testeur d'intégrité des messages avec latence et indépendance des subscribers"""
    
    def __init__(self, proxy_host='localhost', proxy_port=6380, log_level=logging.INFO):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.log_level = log_level
        logger.setLevel(log_level)
        self.test_results = {}
        self.message_tracking = defaultdict(lambda: {
            "sent_time": None, "size_kb": None, "publisher_id": None,
            "expected_message": None,  # Stocke le message attendu pour comparaison
            "receivers": defaultdict(list)  # Par receiver_id: list of receive_times
        })
        self.received_sets = defaultdict(set)  # Par receiver_id: set de message_ids reçus
        
    def generate_test_message(self, size_kb: int, message_id: str) -> str:
        """Génère un message de test avec une taille spécifique"""
        logger.debug(f"🧪 Génération message: ID={message_id}, taille={size_kb}KB")
        
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
        
        # Calculer la taille actuelle et ajouter padding
        target_size = size_kb * 1024
        current_json = json.dumps(base_data)
        current_size = len(current_json.encode('utf-8'))
        
        if current_size < target_size:
            padding_size = target_size - current_size - 100  # Marge plus large
            padding_data = ''.join(random.choices(string.ascii_letters + string.digits, k=padding_size))
            base_data["padding"] = padding_data
        
        # Ajouter checksum
        message_json = json.dumps(base_data, sort_keys=True)
        checksum = hashlib.sha256(message_json.encode('utf-8')).hexdigest()
        base_data["checksum"] = checksum
        
        final_message = json.dumps(base_data)
        actual_size = len(final_message.encode('utf-8')) / 1024
        
        if abs(actual_size - size_kb) > 5:  # Tolérance 5KB
            logger.warning(f"⚠️ Taille réelle {actual_size:.1f}KB ≠ cible {size_kb}KB pour {message_id}")
        
        logger.debug(f"✅ Message généré: {actual_size:.1f}KB")
        return final_message
    
    def compute_similarity_percent(self, expected: str, received: str) -> float:
        """Calcule le % de correspondance entre deux strings (byte-à-byte via difflib)"""
        seq_matcher = difflib.SequenceMatcher(None, expected, received)
        return seq_matcher.ratio() * 100
    
    def verify_message_integrity(self, received_message: str, expected_message_id: str, expected_message: Optional[str] = None) -> Tuple[bool, Dict]:
        """Vérifie l'intégrité avec % de correspondance"""
        logger.info(f"🔍 Vérification intégrité: ID={expected_message_id}")
        
        try:
            data = json.loads(received_message)
            
            if data.get("message_id") != expected_message_id:
                return False, {"error": "Message ID mismatch", "similarity_percent": 0.0}
            
            # Vérifier checksum
            received_checksum = data.pop("checksum", None)
            if not received_checksum:
                return False, {"error": "Missing checksum", "similarity_percent": 0.0}
            
            data_without_checksum = json.dumps(data, sort_keys=True)
            calculated_checksum = hashlib.sha256(data_without_checksum.encode('utf-8')).hexdigest()
            
            if received_checksum != calculated_checksum:
                # Calculer % correspondance si message attendu disponible
                sim_percent = 0.0
                if expected_message:
                    sim_percent = self.compute_similarity_percent(expected_message, received_message)
                    logger.warning(f"⚠️ Checksum mismatch pour {expected_message_id}: attendu={calculated_checksum[:8]}..., reçu={received_checksum[:8]}..., similarité={sim_percent:.1f}%")
                return False, {"error": "Checksum mismatch", "similarity_percent": sim_percent}
            
            # Vérifier séquence
            test_data = data.get("test_data", {})
            sequence = test_data.get("sequence", [])
            if sequence != list(range(100)):
                return False, {"error": "Sequence data corrupted", "similarity_percent": 0.0}
            
            logger.debug(f"✅ Intégrité OK: {expected_message_id}")
            return True, {
                "message_id": data["message_id"],
                "size_kb": test_data.get("size_kb", 0),
                "timestamp": data.get("timestamp", 0),
                "sender": data.get("sender", "unknown"),
                "similarity_percent": 100.0
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error pour {expected_message_id}: {e}")
            return False, {"error": f"JSON decode error: {e}", "similarity_percent": 0.0}
        except Exception as e:
            logger.error(f"❌ Erreur vérification {expected_message_id}: {e}")
            return False, {"error": f"Verification error: {e}", "similarity_percent": 0.0}
    
    def parse_pubsub_message(self, data: bytes) -> Optional[str]:
        """Parser RESP robuste pour messages Pub/Sub"""
        logger.debug("📄 Parsing RESP...")
        try:
            # Parser simple RESP (itératif pour *3 ... $... \r\n)
            i = 0
            lines = data.decode('utf-8', errors='replace').split('\r\n')
            
            while i < len(lines):
                line = lines[i].strip()
                if line == '*3':  # Message Pub/Sub: *3\r\n$7\r\nmessage\r\n$<len>\r\n<channel>\r\n$<len>\r\n<content>
                    i += 1
                    if i < len(lines) and lines[i].startswith('$7') and lines[i+1] == 'message':
                        i += 3  # Skip to channel len
                        if i < len(lines) and lines[i].startswith('$'):
                            channel_len = int(lines[i][1:])
                            i += 1
                            if i < len(lines):
                                i += 1  # Skip channel
                            if i < len(lines) and lines[i].startswith('$'):
                                msg_len = int(lines[i][1:])
                                i += 1
                                if i < len(lines):
                                    content = lines[i]
                                    if len(content) == msg_len:
                                        logger.debug(f"✅ RESP parsé: {len(content)} bytes")
                                        return content
                i += 1
            
            # Fallback: chercher JSON
            for line in lines:
                if line.startswith('{') and line.endswith('}'):
                    logger.warning("⚠️ Fallback JSON parsing utilisé")
                    return line
            
            logger.error("❌ Échec parsing RESP")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur parsing RESP: {e}")
            return None
    
    async def create_publisher(self, publisher_id: str, channel: str, message_sizes: List[int], messages_per_size: int):
        """Publisher avec stockage du message attendu pour vérif. indépendante"""
        logger.info(f"📤 Démarrage publisher {publisher_id} sur {channel}")
        try:
            reader, writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)
            
            sent_messages = []
            
            for size_kb in message_sizes:
                for i in range(messages_per_size):
                    message_id = f"pub_{publisher_id}_size_{size_kb}kb_msg_{i}"
                    
                    message_content = self.generate_test_message(size_kb, message_id)
                    
                    send_time = time.time()
                    self.message_tracking[message_id]["sent_time"] = send_time
                    self.message_tracking[message_id]["size_kb"] = size_kb
                    self.message_tracking[message_id]["publisher_id"] = publisher_id
                    self.message_tracking[message_id]["expected_message"] = message_content  # Pour comparaison
                    
                    # Commande PUBLISH RESP
                    publish_cmd = f"*3\r\n$7\r\nPUBLISH\r\n${len(channel)}\r\n{channel}\r\n${len(message_content)}\r\n{message_content}\r\n"
                    
                    writer.write(publish_cmd.encode())
                    await writer.drain()
                    
                    # Lire réponse (nombre de receivers)
                    response = await reader.read(1024)
                    logger.debug(f"📤 Réponse PUBLISH: {response.decode().strip()}")
                    
                    sent_messages.append({
                        "message_id": message_id,
                        "size_kb": size_kb,
                        "send_time": send_time
                    })
                    
                    logger.info(f"📤 {publisher_id} envoyé: {message_id} ({size_kb}KB)")
                    
                    await asyncio.sleep(0.1)  # Pause anti-overload
            
            writer.close()
            await writer.wait_closed()
            
            logger.info(f"✅ Publisher {publisher_id} terminé: {len(sent_messages)} messages")
            return sent_messages
            
        except Exception as e:
            logger.error(f"❌ Erreur publisher {publisher_id}: {e}")
            return []
    
    async def create_receiver(self, receiver_id: str, channel: str, expected_message_count: int, timeout: int = 30):
        """Receiver indépendant : track set de message_ids pour vérif. 100% réception"""
        logger.info(f"📥 Démarrage receiver {receiver_id} sur {channel}, attente {expected_message_count} msgs")
        try:
            reader, writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)
            
            # Subscribe avec retry
            subscribe_cmd = f"*2\r\n$9\r\nSUBSCRIBE\r\n${len(channel)}\r\n{channel}\r\n"
            writer.write(subscribe_cmd.encode())
            await writer.drain()
            
            # Lire confirmation (peut prendre du temps)
            confirm = await asyncio.wait_for(reader.read(1024), timeout=5)
            logger.debug(f"📥 Confirmation subscribe: {confirm.decode().strip()}")
            
            received_messages = []
            start_time = time.time()
            unique_ids = set()  # Pour tracking indépendance
            
            while len(received_messages) < expected_message_count:
                if time.time() - start_time > timeout:
                    logger.warning(f"⏰ Timeout {receiver_id}: {len(received_messages)}/{expected_message_count}")
                    break
                
                try:
                    data = await asyncio.wait_for(reader.read(128*1024), timeout=2.0)  # Buffer plus grand
                    
                    if not data:
                        continue
                    
                    message_content = self.parse_pubsub_message(data)
                    if not message_content:
                        continue
                    
                    receive_time = time.time()
                    
                    # Extraire ID
                    try:
                        temp_data = json.loads(message_content)
                        message_id = temp_data.get("message_id", "unknown")
                    except:
                        message_id = "parse_error"
                        logger.warning(f"⚠️ ID inconnu pour message reçu par {receiver_id}")
                    
                    unique_ids.add(message_id)
                    self.received_sets[receiver_id].add(message_id)
                    
                    # Vérif. avec message attendu
                    expected_msg = self.message_tracking[message_id].get("expected_message")
                    is_valid, verification_result = self.verify_message_integrity(
                        message_content, message_id, expected_msg
                    )
                    
                    if is_valid:
                        sent_time = self.message_tracking[message_id]["sent_time"]
                        latency_ms = (receive_time - sent_time) * 1000
                        
                        self.message_tracking[message_id]["receivers"][receiver_id].append(receive_time)
                        
                        received_messages.append({
                            "message_id": message_id,
                            "receiver_id": receiver_id,
                            "receive_time": receive_time,
                            "latency_ms": latency_ms,
                            "size_kb": verification_result.get("size_kb", 0),
                            "is_valid": True,
                            "similarity_percent": verification_result.get("similarity_percent", 100.0)
                        })
                        
                        logger.info(f"✅ {receiver_id} reçu: {message_id} (latence: {latency_ms:.1f}ms, similarité: 100%)")
                    else:
                        sim_percent = verification_result.get("similarity_percent", 0.0)
                        received_messages.append({
                            "message_id": message_id,
                            "receiver_id": receiver_id,
                            "receive_time": receive_time,
                            "is_valid": False,
                            "error": verification_result.get("error"),
                            "similarity_percent": sim_percent
                        })
                        logger.error(f"❌ {receiver_id} corrompu: {message_id} (similarité: {sim_percent:.1f}%, erreur: {verification_result.get('error')})")
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"❌ Erreur lecture {receiver_id}: {e}")
                    continue
            
            # Log indépendance partielle
            coverage = len(unique_ids) / expected_message_count * 100 if expected_message_count > 0 else 0
            logger.info(f"📊 {receiver_id} : {len(unique_ids)}/{expected_message_count} IDs uniques ({coverage:.1f}% couverture)")
            
            writer.close()
            await writer.wait_closed()
            
            return received_messages
            
        except Exception as e:
            logger.error(f"❌ Erreur receiver {receiver_id}: {e}")
            return []
    
    async def run_message_integrity_test(self, test_config: Dict):
        """Lance le test avec focus sur indépendance"""
        print(f"\n🧪 Test: {test_config['name']}")
        print("=" * 50)
        
        channel = test_config['channel']
        publishers_count = test_config['publishers']
        receivers_count = test_config['receivers']
        message_sizes = test_config['message_sizes']
        messages_per_size = test_config['messages_per_size']
        
        total_messages = publishers_count * len(message_sizes) * messages_per_size
        
        print(f"📊 Config: Publishers={publishers_count}, Receivers={receivers_count}, Tailles={message_sizes}KB, Msgs/taille={messages_per_size}, Total={total_messages}")
        
        self.message_tracking.clear()
        self.received_sets.clear()
        
        # Démarrer receivers
        receiver_tasks = [asyncio.create_task(
            self.create_receiver(f"recv_{i}", channel, total_messages, timeout=60)
        ) for i in range(receivers_count)]
        
        await asyncio.sleep(2)  # Temps pour abonnements
        
        # Publishers
        publisher_tasks = [asyncio.create_task(
            self.create_publisher(f"pub_{i}", channel, message_sizes, messages_per_size)
        ) for i in range(publishers_count)]
        
        publisher_results = await asyncio.gather(*publisher_tasks, return_exceptions=True)
        await asyncio.sleep(10)  # Temps pour réceptions
        
        for task in receiver_tasks:
            task.cancel()
        receiver_results = await asyncio.gather(*receiver_tasks, return_exceptions=True)
        
        # Analyse
        return self.analyze_results(test_config, publisher_results, receiver_results)
    
    def analyze_results(self, test_config: Dict, publisher_results: List, receiver_results: List) -> Dict:
        """Analyse avec % correspondance et indépendance"""
        analysis = {
            "test_name": test_config['name'],
            "config": test_config,
            "summary": {},
            "latency_stats": {},
            "integrity_stats": {},
            "independence_stats": {},  # Nouveau : indépendance
            "similarity_stats": {}  # Nouveau : % correspondance
        }
        
        # Sent
        total_sent = sum(len(res) for res in publisher_results if isinstance(res, list))
        
        # Received
        total_received = 0
        valid_messages = 0
        corrupted_messages = 0
        all_similarities = []  # Pour stats globales
        latencies_by_size = defaultdict(list)
        reception_count_per_message = defaultdict(int)
        receiver_coverages = {}  # % couverture par receiver
        
        for result in receiver_results:
            if isinstance(result, list):
                for msg in result:
                    total_received += 1
                    if msg.get("is_valid", False):
                        valid_messages += 1
                        latency = msg.get("latency_ms", 0)
                        size_kb = msg.get("size_kb", 0)
                        sim_percent = msg.get("similarity_percent", 100.0)
                        latencies_by_size[size_kb].append(latency)
                        all_similarities.append(sim_percent)
                        reception_count_per_message[msg["message_id"]] += 1
                    else:
                        corrupted_messages += 1
                        all_similarities.append(msg.get("similarity_percent", 0.0))
        
        expected_total_receptions = total_sent * test_config['receivers']
        delivery_rate = (total_received / expected_total_receptions * 100) if expected_total_receptions > 0 else 0
        integrity_rate = (valid_messages / total_received * 100) if total_received > 0 else 0
        avg_similarity = statistics.mean(all_similarities) if all_similarities else 0
        
        analysis["summary"] = {
            "messages_sent": total_sent,
            "total_receptions": total_received,
            "expected_receptions": expected_total_receptions,
            "valid_messages": valid_messages,
            "corrupted_messages": corrupted_messages,
            "delivery_rate_percent": delivery_rate,
            "integrity_rate_percent": integrity_rate
        }
        
        # Latence
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
        
        # Intégrité (duplicates/losses)
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
        
        # Indépendance : % de receivers qui ont reçu 100% des messages
        for receiver_id, received_ids in self.received_sets.items():
            coverage = len(received_ids) / total_sent * 100 if total_sent > 0 else 0
            receiver_coverages[receiver_id] = coverage
            logger.info(f"🎯 Indépendance {receiver_id}: {coverage:.1f}% des messages reçus (comme s'il était seul)")
        
        full_independence_rate = sum(1 for cov in receiver_coverages.values() if cov >= 99.0) / len(receiver_coverages) * 100 if receiver_coverages else 0  # Tolérance 1%
        analysis["independence_stats"] = {
            "full_independence_rate_percent": full_independence_rate,
            "receiver_coverages": receiver_coverages,
            "avg_coverage_percent": statistics.mean(receiver_coverages.values()) if receiver_coverages else 0
        }
        
        # Similarité
        analysis["similarity_stats"] = {
            "avg_similarity_percent": avg_similarity,
            "min_similarity_percent": min(all_similarities) if all_similarities else 0,
            "max_similarity_percent": max(all_similarities) if all_similarities else 0
        }
        
        return analysis
    
    def print_analysis(self, analysis: Dict):
        """Affichage clair avec focus objectifs"""
        print(f"\n📊 RÉSULTATS - {analysis['test_name']}")
        print("=" * 60)
        
        summary = analysis["summary"]
        print(f"📤 Envoyés: {summary['messages_sent']:,}")
        print(f"📥 Reçus: {summary['total_receptions']:,} / {summary['expected_receptions']:,} ({summary['delivery_rate_percent']:.1f}%)")
        print(f"✅ Valides: {summary['valid_messages']:,} / {summary['total_receptions']:,} ({summary['integrity_rate_percent']:.1f}%)")
        print(f"❌ Corrompus: {summary['corrupted_messages']:,}")
        
        # Objectif 1: Latence
        print(f"\n⏱️ LATENCE PAR TAILLE:")
        for size, stats in analysis["latency_stats"].items():
            print(f"  {size}: avg={stats['avg_ms']:.1f}ms, p99={stats['p99_ms']:.1f}ms")
        
        # Objectif 2: Intégrité
        integrity = analysis["integrity_stats"]
        print(f"\n🛡️ INTÉGRITÉ:")
        print(f"  Parfaites: {integrity['perfect_delivery_messages']:,}")
        print(f"  Dupliqués: {integrity['total_duplicates']:,}, Perdus: {integrity['total_losses']:,}")
        
        # Objectif 3: % Correspondance
        similarity = analysis["similarity_stats"]
        print(f"\n🔍 CORRESPONDANCE:")
        print(f"  Moyenne: {similarity['avg_similarity_percent']:.1f}%, Min: {similarity['min_similarity_percent']:.1f}%")
        
        # Objectif 4: Indépendance
        independence = analysis["independence_stats"]
        print(f"\n🎯 INDÉPENDANCE SUBSCRIBERS (chacun comme seul):")
        print(f"  Taux complet: {independence['full_independence_rate_percent']:.1f}% des receivers à 100%")
        for rid, cov in independence['receiver_coverages'].items():
            print(f"  {rid}: {cov:.1f}%")

async def main():
    """Fonction principale"""
    print("🚀 TESTS D'INTÉGRITÉ, LATENCE ET INDÉPENDANCE")
    print("=" * 50)
    
    tester = MessageIntegrityTester(log_level=logging.INFO)  # Ou DEBUG pour plus de détails
    
    test_configs = [
        {
            "name": "Small Messages (1-10KB)",
            "channel": "test/integrity/small",
            "publishers": 3,
            "receivers": 5,
            "message_sizes": [1, 5, 10],
            "messages_per_size": 5
        },
        {
            "name": "Medium Messages (50-100KB)",
            "channel": "test/integrity/medium", 
            "publishers": 2,
            "receivers": 4,
            "message_sizes": [50, 100],
            "messages_per_size": 3
        },
        {
            "name": "Large Messages (500KB-1MB)",
            "channel": "test/integrity/large",
            "publishers": 2,
            "receivers": 3,
            "message_sizes": [500, 1000],
            "messages_per_size": 2
        },
        {
            "name": "Mixed Load",
            "channel": "test/integrity/mixed",
            "publishers": 5,
            "receivers": 8,
            "message_sizes": [1, 10, 50, 100, 500],
            "messages_per_size": 2
        }
    ]
    
    all_results = []
    
    for config in test_configs:
        try:
            result = await tester.run_message_integrity_test(config)
            all_results.append(result)
            tester.print_analysis(result)
            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"❌ Erreur test {config['name']}: {e}")
    
    # Résumé global
    print(f"\n🏆 RÉSUMÉ GLOBAL")
    print("=" * 30)
    
    total_sent = sum(r["summary"]["messages_sent"] for r in all_results)
    total_received = sum(r["summary"]["total_receptions"] for r in all_results)
    total_valid = sum(r["summary"]["valid_messages"] for r in all_results)
    
    print(f"📊 Envoyés: {total_sent:,}, Reçus: {total_received:,}, Valides: {total_valid:,}")
    print(f"📊 Intégrité globale: {(total_valid/total_received*100):.1f}%")
    
    # Sauvegarde
    timestamp = int(time.time())
    with open(f"/tmp/integrity_test_results_{timestamp}.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n💾 Résultats: /tmp/integrity_test_results_{timestamp}.json")

if __name__ == "__main__":
    asyncio.run(main())