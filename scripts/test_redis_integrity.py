#!/usr/bin/env python3
"""
Test d'intégrité complet pour le proxy Redis avec système binaire.
Vérifie que les corruptions sont complètement éliminées.
"""

import redis
import json
import time
import hashlib
import random
import string
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

def generate_test_data(size_category):
    """Génère des données de test de différentes tailles"""
    if size_category == "small":
        # Messages de 1-10KB
        size = random.randint(1024, 10*1024)
    elif size_category == "medium":
        # Messages de 10-100KB
        size = random.randint(10*1024, 100*1024)
    elif size_category == "large":
        # Messages de 100KB-1MB
        size = random.randint(100*1024, 1024*1024)
    else:
        size = 1024
    
    # Générer du contenu JSON complexe
    content = {
        "test_id": f"test_{int(time.time()*1000000)}_{random.randint(1000,9999)}",
        "timestamp": time.time(),
        "category": size_category,
        "data": {
            "payload": "".join(random.choices(string.ascii_letters + string.digits + "àéèêëïîôöùûüÿç", k=size-500)),
            "metadata": {
                "version": "1.0",
                "encoding": "utf-8",
                "special_chars": "héllo wörld! 🌟✨🎉",
                "numbers": [1, 2, 3.14159, -42, 1e10],
                "nested": {
                    "deep": {
                        "value": "test_value_with_unicode_ñáéíóú"
                    }
                }
            }
        },
        "checksum": ""
    }
    
    # Calculer le checksum avant sérialisation
    content_for_checksum = json.dumps(content, ensure_ascii=False, sort_keys=True)
    content["checksum"] = hashlib.sha256(content_for_checksum.encode('utf-8')).hexdigest()
    
    return json.dumps(content, ensure_ascii=False)

def verify_message_integrity(original_json, received_json):
    """Vérifie l'intégrité d'un message"""
    try:
        original_data = json.loads(original_json)
        received_data = json.loads(received_json)
        
        # Vérification du checksum
        received_checksum = received_data.get("checksum", "")
        
        # Recalculer le checksum côté réception
        received_data_copy = received_data.copy()
        received_data_copy["checksum"] = ""
        content_for_checksum = json.dumps(received_data_copy, ensure_ascii=False, sort_keys=True)
        calculated_checksum = hashlib.sha256(content_for_checksum.encode('utf-8')).hexdigest()
        
        # Comparaisons
        checksum_match = received_checksum == calculated_checksum
        content_match = original_data == received_data
        
        return {
            "intact": checksum_match and content_match,
            "checksum_match": checksum_match,
            "content_match": content_match,
            "original_size": len(original_json),
            "received_size": len(received_json),
            "size_match": len(original_json) == len(received_json)
        }
    
    except Exception as e:
        return {
            "intact": False,
            "error": str(e),
            "original_size": len(original_json) if original_json else 0,
            "received_size": len(received_json) if received_json else 0
        }

def test_single_message(client, channel, test_data, test_id):
    """Test un seul message"""
    try:
        # Publier le message
        start_time = time.time()
        result = client.publish(channel, test_data)
        publish_time = time.time() - start_time
        
        return {
            "test_id": test_id,
            "success": True,
            "publish_time": publish_time,
            "subscribers": result,
            "message_size": len(test_data)
        }
    
    except Exception as e:
        return {
            "test_id": test_id,
            "success": False,
            "error": str(e),
            "message_size": len(test_data) if test_data else 0
        }

def test_subscriber(channel, expected_messages, timeout=30):
    """Thread subscriber pour recevoir et vérifier les messages"""
    try:
        client = redis.Redis(host='localhost', port=6380, decode_responses=False)
        pubsub = client.pubsub()
        pubsub.subscribe(channel)
        
        received_messages = []
        start_time = time.time()
        
        print(f"📡 Subscriber démarré sur {channel}, attente de {expected_messages} messages...")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                received_messages.append({
                    "data": message['data'].decode('utf-8'),
                    "channel": message['channel'].decode('utf-8'),
                    "timestamp": time.time()
                })
                
                print(f"✅ Message reçu {len(received_messages)}/{expected_messages} sur {channel}")
                
                if len(received_messages) >= expected_messages:
                    break
            
            # Timeout de sécurité
            if time.time() - start_time > timeout:
                print(f"⚠️ Timeout atteint pour {channel}")
                break
        
        pubsub.close()
        client.close()
        
        return received_messages
    
    except Exception as e:
        print(f"❌ Erreur dans subscriber {channel}: {e}")
        return []

def run_integrity_test():
    """Lance le test d'intégrité complet"""
    print("🧪 TEST D'INTÉGRITÉ DU PROXY REDIS")
    print("=" * 50)
    
    # Configuration du test
    test_cases = [
        {"category": "small", "count": 50, "channel": "test/integrity/small"},
        {"category": "medium", "count": 20, "channel": "test/integrity/medium"},
        {"category": "large", "count": 10, "channel": "test/integrity/large"}
    ]
    
    total_tests = sum(case["count"] for case in test_cases)
    print(f"📊 Total: {total_tests} messages à tester")
    print()
    
    # Stockage des données de test
    test_data_store = {}
    
    # Démarrer les subscribers
    subscriber_futures = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        for case in test_cases:
            future = executor.submit(test_subscriber, case["channel"], case["count"])
            subscriber_futures[case["channel"]] = future
        
        # Attendre un peu que les subscribers soient prêts
        time.sleep(2)
        
        # Client pour publisher
        publisher_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        
        # Lancer les tests par catégorie
        all_publish_results = []
        
        for case in test_cases:
            print(f"🚀 Test {case['category']} - {case['count']} messages sur {case['channel']}")
            
            category_results = []
            category_data = []
            
            # Générer et publier les messages
            for i in range(case["count"]):
                test_data = generate_test_data(case["category"])
                test_id = f"{case['category']}_{i+1}"
                
                # Stocker pour vérification ultérieure
                test_data_store[test_id] = test_data
                category_data.append((test_id, test_data))
                
                # Publier
                result = test_single_message(publisher_client, case["channel"], test_data, test_id)
                category_results.append(result)
                
                if (i + 1) % 10 == 0:
                    print(f"  📤 {i+1}/{case['count']} messages publiés...")
            
            all_publish_results.extend(category_results)
            print(f"✅ {case['category']}: {case['count']} messages publiés")
        
        publisher_client.close()
        
        # Attendre les résultats des subscribers
        print("\n📡 Attente des messages reçus...")
        all_received = {}
        
        for channel, future in subscriber_futures.items():
            try:
                received = future.result(timeout=40)
                all_received[channel] = received
                print(f"✅ {channel}: {len(received)} messages reçus")
            except Exception as e:
                print(f"❌ Erreur {channel}: {e}")
                all_received[channel] = []
    
    # Analyse des résultats
    print("\n🔍 ANALYSE DES RÉSULTATS")
    print("=" * 30)
    
    # Statistiques de publication
    successful_publishes = sum(1 for r in all_publish_results if r["success"])
    failed_publishes = len(all_publish_results) - successful_publishes
    
    print(f"📤 Publications: {successful_publishes}/{len(all_publish_results)} réussies")
    if failed_publishes > 0:
        print(f"❌ Échecs de publication: {failed_publishes}")
    
    # Vérification de l'intégrité
    total_integrity_checks = 0
    intact_messages = 0
    corrupted_messages = 0
    
    for case in test_cases:
        channel = case["channel"]
        received_messages = all_received.get(channel, [])
        
        print(f"\n📊 {case['category'].upper()}:")
        print(f"  Envoyés: {case['count']}")
        print(f"  Reçus: {len(received_messages)}")
        
        # Vérifier l'intégrité de chaque message reçu
        for i, received_msg in enumerate(received_messages):
            test_id = f"{case['category']}_{i+1}"
            
            if test_id in test_data_store:
                original_data = test_data_store[test_id]
                received_data = received_msg["data"]
                
                integrity_result = verify_message_integrity(original_data, received_data)
                total_integrity_checks += 1
                
                if integrity_result["intact"]:
                    intact_messages += 1
                else:
                    corrupted_messages += 1
                    print(f"  ❌ Message {test_id} corrompu:")
                    print(f"     Checksum: {integrity_result.get('checksum_match', False)}")
                    print(f"     Contenu: {integrity_result.get('content_match', False)}")
                    print(f"     Taille: {integrity_result.get('original_size', 0)} -> {integrity_result.get('received_size', 0)}")
                    if "error" in integrity_result:
                        print(f"     Erreur: {integrity_result['error']}")
    
    # Résumé final
    print(f"\n🎯 RÉSUMÉ FINAL")
    print("=" * 20)
    print(f"Messages testés: {total_integrity_checks}")
    print(f"Messages intacts: {intact_messages}")
    print(f"Messages corrompus: {corrupted_messages}")
    
    if total_integrity_checks > 0:
        integrity_rate = (intact_messages / total_integrity_checks) * 100
        print(f"Taux d'intégrité: {integrity_rate:.2f}%")
        
        if integrity_rate == 100.0:
            print("🎉 SUCCÈS TOTAL! Aucune corruption détectée!")
            return True
        else:
            print(f"⚠️ {corrupted_messages} corruptions détectées")
            return False
    else:
        print("❌ Aucun test d'intégrité effectué")
        return False

if __name__ == "__main__":
    success = run_integrity_test()
    sys.exit(0 if success else 1)