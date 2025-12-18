#!/usr/bin/env python3
"""
Script de test pour vérifier si le coordinateur continue à recevoir les messages Redis
après un certain temps. Ce script publie des messages à intervalle régulier et vérifie
la réception.
"""

import os
import sys
import time
import django
from datetime import datetime

# Configuration Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coordinator_project.settings')
django.setup()

from redis_communication.client import RedisClient
from redis_communication.message import Message

# Compteurs
messages_sent = 0
messages_received = 0
last_received_time = None
test_start_time = time.time()

def test_handler(channel: str, message: Message):
    """Handler qui compte les messages reçus"""
    global messages_received, last_received_time
    messages_received += 1
    last_received_time = time.time()
    elapsed = last_received_time - test_start_time
    print(f"✅ [{int(elapsed)}s] Message #{messages_received} reçu: {message.data.get('counter')}")

def main():
    global messages_sent
    
    print("=" * 80)
    print("🔬 TEST DE DURABILITÉ DE LA CONNEXION REDIS")
    print("=" * 80)
    print(f"Début du test: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Ce test va publier un message toutes les 10 secondes")
    print("et vérifier si le coordinateur continue à les recevoir.")
    print("Appuyez sur Ctrl+C pour arrêter.")
    print("=" * 80)
    print()
    
    try:
        # Initialiser le client Redis
        redis_client = RedisClient.get_instance()
        
        if not redis_client.running:
            print("⚙️  Démarrage du client Redis...")
            redis_client.start()
            time.sleep(2)  # Attendre que la connexion soit établie
        
        # S'abonner au canal de test
        test_channel = "test/heartbeat"
        print(f"📡 Abonnement au canal: {test_channel}")
        redis_client.subscribe(test_channel, test_handler)
        time.sleep(1)
        
        print("✅ Client Redis initialisé et abonné")
        print()
        
        # Boucle de test
        interval = 10  # secondes
        max_no_response_time = 60  # Alerter si pas de réponse pendant 60s
        
        while True:
            messages_sent += 1
            elapsed = int(time.time() - test_start_time)
            
            # Publier un message
            data = {
                'counter': messages_sent,
                'timestamp': datetime.now().isoformat(),
                'elapsed_seconds': elapsed,
                'test': 'heartbeat'
            }
            
            print(f"📤 [{elapsed}s] Envoi du message #{messages_sent}...")
            redis_client.publish(test_channel, data)
            
            # Attendre l'intervalle
            time.sleep(interval)
            
            # Vérifier si on reçoit toujours les messages
            if last_received_time:
                time_since_last = time.time() - last_received_time
                
                if time_since_last > max_no_response_time:
                    print()
                    print("⚠️" * 40)
                    print(f"❌ PROBLÈME DÉTECTÉ!")
                    print(f"   Aucun message reçu depuis {int(time_since_last)}s")
                    print(f"   Messages envoyés: {messages_sent}")
                    print(f"   Messages reçus: {messages_received}")
                    print(f"   Perte: {messages_sent - messages_received} messages")
                    print(f"   Temps écoulé depuis le début: {elapsed}s ({elapsed/60:.1f} minutes)")
                    print("⚠️" * 40)
                    print()
            
            # Afficher un résumé toutes les minutes
            if messages_sent % 6 == 0:  # Toutes les 60 secondes (6 * 10s)
                print()
                print("-" * 80)
                print(f"📊 RÉSUMÉ après {elapsed}s ({elapsed/60:.1f} min)")
                print(f"   Messages envoyés: {messages_sent}")
                print(f"   Messages reçus: {messages_received}")
                print(f"   Taux de réception: {(messages_received/messages_sent*100):.1f}%")
                if last_received_time:
                    print(f"   Dernier message reçu il y a: {int(time.time() - last_received_time)}s")
                print("-" * 80)
                print()
    
    except KeyboardInterrupt:
        print()
        print("=" * 80)
        print("🛑 Arrêt du test")
        elapsed = int(time.time() - test_start_time)
        print()
        print("📊 RÉSUMÉ FINAL")
        print(f"   Durée totale: {elapsed}s ({elapsed/60:.1f} minutes)")
        print(f"   Messages envoyés: {messages_sent}")
        print(f"   Messages reçus: {messages_received}")
        print(f"   Messages perdus: {messages_sent - messages_received}")
        print(f"   Taux de réception: {(messages_received/messages_sent*100):.1f}%")
        
        if messages_received < messages_sent:
            print()
            print(f"⚠️  CONCLUSION: Le coordinateur a cessé de recevoir les messages")
            if last_received_time:
                time_since_last = time.time() - last_received_time
                time_until_stop = last_received_time - test_start_time
                print(f"   - A reçu des messages pendant: {int(time_until_stop)}s ({time_until_stop/60:.1f} min)")
                print(f"   - Plus de réception depuis: {int(time_since_last)}s")
        else:
            print()
            print(f"✅ CONCLUSION: Le coordinateur a reçu tous les messages sans interruption")
        
        print("=" * 80)
        redis_client.stop()
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
