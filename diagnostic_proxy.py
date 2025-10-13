#!/usr/bin/env python3
"""
Script de test pour proxy Redis Pub/Sub fait maison.
Vérifie que chaque message reçu correspond EXACTEMENT à celui envoyé.
S'arrête au premier problème détecté.
"""

import redis
import json
import hashlib
import time
import threading
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configuration
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 6380
CHANNEL = "test/channel"
TEST_TIMEOUT = 15

# Couleurs pour l'affichage
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def calculate_checksum(data: str) -> str:
    """Calcule le checksum SHA256 d'une chaîne"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def create_test_message(msg_id: int, payload_size: int) -> Dict[str, Any]:
    """Crée un message de test avec le format JSON spécifié"""
    # Créer un payload de la taille demandée avec un pattern reconnaissable
    # Pour détecter la corruption, on alterne les caractères
    payload = ""
    for i in range(payload_size):
        payload += chr(65 + (i % 26))  # A-Z qui se répète
    
    checksum = calculate_checksum(payload)
    
    message_data = {
        "msg_id": msg_id,
        "size": payload_size,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload,
        "sender": "stress_test",
        "message_type": "test",
        "checksum": checksum
    }
    
    return message_data

def compare_messages_detailed(received: Dict[str, Any], expected: Dict[str, Any]) -> Optional[str]:
    """
    Compare deux messages en détail.
    Retourne None si identiques, sinon retourne le message d'erreur.
    """
    print("Comparaison détaillée des messages: \n recu: ", received, "\n attendu: ", expected)
    # 1. Vérifier que tous les champs sont présents
    expected_fields = ["msg_id", "size", "timestamp", "payload", "sender", "message_type", "checksum"]
    for field in expected_fields:
        if field not in received:
            return f"❌ Champ manquant: '{field}'"
    
    # 2. Vérifier msg_id
    if received["msg_id"] != expected["msg_id"]:
        return f"❌ msg_id différent: reçu={received['msg_id']}, attendu={expected['msg_id']}"
    
    # 3. Vérifier la taille déclarée
    if received["size"] != expected["size"]:
        return f"❌ Champ 'size' différent: reçu={received['size']}, attendu={expected['size']}"
    
    # 4. Vérifier le payload - C'EST LE PLUS IMPORTANT
    received_payload = received.get("payload", "")
    expected_payload = expected["payload"]
    
    if len(received_payload) != len(expected_payload):
        diff = len(received_payload) - len(expected_payload)
        if diff > 0:
            error_msg = f"❌ PAYLOAD TROP LONG: {diff} octets EN TROP\n"
            error_msg += f"   Taille attendue: {len(expected_payload)} octets\n"
            error_msg += f"   Taille reçue: {len(received_payload)} octets\n"
            error_msg += f"   🔴 PROBLÈME: COUPLAGE TCP - Le proxy a fusionné plusieurs messages\n"
            error_msg += f"\n   Début du payload reçu (500 premiers chars):\n   {received_payload[:500]}\n"
            error_msg += f"\n   Fin du payload reçu (500 derniers chars):\n   ...{received_payload[-500:]}"
            return error_msg
        else:
            error_msg = f"❌ PAYLOAD TRONQUÉ: {-diff} octets MANQUANTS\n"
            error_msg += f"   Taille attendue: {len(expected_payload)} octets\n"
            error_msg += f"   Taille reçue: {len(received_payload)} octets\n"
            error_msg += f"   🔴 PROBLÈME: DÉCOUPAGE TCP - Le proxy n'a pas lu tout le message\n"
            error_msg += f"\n   Payload reçu (complet):\n   {received_payload[:1000]}\n"
            error_msg += f"\n   Payload attendu (début):\n   {expected_payload[:1000]}"
            return error_msg
    
    # 5. Comparer byte par byte
    if received_payload != expected_payload:
        # Trouver la première différence
        for i in range(len(received_payload)):
            if received_payload[i] != expected_payload[i]:
                error_msg = f"❌ PAYLOAD CORROMPU: Différence à l'octet {i}\n"
                error_msg += f"   Caractère reçu: '{received_payload[i]}' (ASCII {ord(received_payload[i])})\n"
                error_msg += f"   Caractère attendu: '{expected_payload[i]}' (ASCII {ord(expected_payload[i])})\n"
                error_msg += f"   🔴 PROBLÈME: CORRUPTION - Le proxy modifie les données\n"
                error_msg += f"\n   Contexte (50 chars autour):\n"
                error_msg += f"   Reçu:   ...{received_payload[max(0,i-25):i+25]}...\n"
                error_msg += f"   Attendu:...{expected_payload[max(0,i-25):i+25]}..."
                return error_msg
    
    # 6. Vérifier le checksum
    calculated_checksum = calculate_checksum(received_payload)
    if received["checksum"] != calculated_checksum:
        error_msg = f"❌ CHECKSUM INVALIDE\n"
        error_msg += f"   Checksum dans le message: {received['checksum'][:32]}...\n"
        error_msg += f"   Checksum calculé du payload: {calculated_checksum[:32]}...\n"
        error_msg += f"   🔴 PROBLÈME: Le payload a été modifié"
        return error_msg
    
    # 7. Vérifier les autres champs (moins critiques)
    if received.get("sender") != expected["sender"]:
        return f"❌ Champ 'sender' différent: reçu={received.get('sender')}, attendu={expected['sender']}"
    
    if received.get("message_type") != expected["message_type"]:
        return f"❌ Champ 'message_type' différent: reçu={received.get('message_type')}, attendu={expected['message_type']}"
    
    # Tout est identique !
    return None

class RedisProxyTester:
    def __init__(self, host: str, port: int, channel: str):
        self.host = host
        self.port = port
        self.channel = channel
        self.received_messages = []
        self.subscriber_ready = threading.Event()
        self.subscriber_error = None
        self.subscriber_thread = None
        self.pubsub = None
        self.stop_flag = threading.Event()
        
    def subscriber_worker(self):
        """Thread qui écoute les messages sur le canal"""
        try:
            sub_client = redis.Redis(host=self.host, port=self.port, decode_responses=False, socket_timeout=5)
            self.pubsub = sub_client.pubsub()
            self.pubsub.subscribe(self.channel)
            
            print(f"{Colors.BLUE}[Subscriber] ✓ Connecté et souscrit au canal '{self.channel}'{Colors.RESET}\n")
            self.subscriber_ready.set()
            
            while not self.stop_flag.is_set():
                try:
                    message = self.pubsub.get_message(timeout=1)
                    if message and message['type'] == 'message':
                        try:
                            data = message['data']
                            if isinstance(data, bytes):
                                data = data.decode('utf-8')
                            
                            msg_obj = json.loads(data)
                            self.received_messages.append({
                                "timestamp": time.time(),
                                "data": msg_obj,
                                "raw_json": data,
                                "raw_size": len(data)
                            })
                            
                        except json.JSONDecodeError as e:
                            print(f"{Colors.RED}[Subscriber] ❌ ERREUR PARSING JSON: {e}{Colors.RESET}")
                            print(f"{Colors.RED}   Données reçues (500 premiers chars):\n   {data[:500]}{Colors.RESET}\n")
                            self.received_messages.append({
                                "timestamp": time.time(),
                                "error": "json_decode_error",
                                "raw_data": data,
                                "exception": str(e)
                            })
                        except Exception as e:
                            print(f"{Colors.RED}[Subscriber] ❌ Erreur inattendue: {e}{Colors.RESET}\n")
                            self.received_messages.append({
                                "timestamp": time.time(),
                                "error": "unknown_error",
                                "exception": str(e)
                            })
                except Exception:
                    pass  # Timeout normal
                    
        except Exception as e:
            self.subscriber_error = e
            print(f"{Colors.RED}[Subscriber] ❌ Erreur fatale: {e}{Colors.RESET}\n")
    
    def start_subscriber(self):
        """Démarre le thread subscriber"""
        self.subscriber_thread = threading.Thread(target=self.subscriber_worker, daemon=True)
        self.subscriber_thread.start()
        
        if not self.subscriber_ready.wait(timeout=5):
            raise TimeoutError("Le subscriber n'a pas pu se connecter")
    
    def publish_message(self, message_data: Dict[str, Any]) -> bool:
        """Publie un message sur le canal"""
        try:
            pub_client = redis.Redis(host=self.host, port=self.port, decode_responses=False, socket_timeout=5)
            json_data = json.dumps(message_data)
            
            result = pub_client.publish(self.channel, json_data)
            return True
        except Exception as e:
            print(f"{Colors.RED}[Publisher] ❌ Erreur: {e}{Colors.RESET}\n")
            return False
    
    def stop(self):
        """Arrête le subscriber"""
        self.stop_flag.set()
        if self.pubsub:
            try:
                self.pubsub.unsubscribe()
                self.pubsub.close()
            except:
                pass

def format_size(size_bytes: int) -> str:
    """Format la taille en unité lisible"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def run_progressive_test():
    """
    Teste progressivement avec des messages de plus en plus grands.
    S'arrête au premier problème détecté.
    """
    print("=" * 80)
    print("TEST PROGRESSIF DU PROXY REDIS PUB/SUB")
    print("=" * 80)
    print(f"Proxy: {PROXY_HOST}:{PROXY_PORT}")
    print(f"Canal: {CHANNEL}")
    print(f"Taille maximale: 10 MB")
    print(f"Objectif: Vérifier que chaque message reçu = message envoyé")
    print("=" * 80)
    print()
    
    tester = RedisProxyTester(PROXY_HOST, PROXY_PORT, CHANNEL)
    
    try:
        # Démarrer le subscriber
        print(f"{Colors.CYAN}📡 Démarrage du subscriber...{Colors.RESET}")
        tester.start_subscriber()
        time.sleep(1)
        
        # Tailles de test progressives jusqu'à 10 MB
        test_sizes = [
            100,           # 100 B
            1024,          # 1 KB
            10 * 1024,     # 10 KB
            100 * 1024,    # 100 KB
            500 * 1024,    # 500 KB
            1024 * 1024,   # 1 MB
            2 * 1024 * 1024,   # 2 MB
            5 * 1024 * 1024,   # 5 MB
            10 * 1024 * 1024,  # 10 MB
        ]
        
        for test_id, size in enumerate(test_sizes, 1):
            print("=" * 80)
            print(f"{Colors.CYAN}TEST {test_id}: Message de {format_size(size)}{Colors.RESET}")
            print("=" * 80)
            
            # Créer le message avec un ID UNIQUE
            expected_msg = create_test_message(test_id, size)
            expected_json = json.dumps(expected_msg)
            
            print(f"📤 Envoi du message {test_id}...")
            print(f"   msg_id: {test_id}")
            print(f"   Taille payload: {size} octets")
            print(f"   Checksum: {expected_msg['checksum'][:32]}...")
            
            # ✅ CORRECTION 1 : Marquer le timestamp avant envoi
            send_time = time.time()
            initial_count = len(tester.received_messages)
            
            # Publier
            if not tester.publish_message(expected_msg):
                print(f"{Colors.RED}❌ Échec de l'envoi{Colors.RESET}\n")
                return False
            
            print(f"{Colors.GREEN}✓ Message publié{Colors.RESET}")
            
            # ✅ CORRECTION 2 : Attendre LE MESSAGE avec le bon msg_id
            print(f"📥 Attente du message avec msg_id={test_id}...")
            timeout = 10
            start_time = time.time()
            found_message = None
            
            while found_message is None:
                if time.time() - start_time > timeout:
                    print(f"{Colors.RED}❌ TIMEOUT: Message {test_id} non reçu après {timeout}s{Colors.RESET}")
                    print(f"{Colors.RED}Messages reçus pendant l'attente:{Colors.RESET}")
                    for msg in tester.received_messages[initial_count:]:
                        if "data" in msg:
                            print(f"   - msg_id={msg['data'].get('msg_id')} (timestamp={msg['timestamp']})")
                    print(f"{Colors.RED}🔴 PROBLÈME: Le proxy ne transmet pas le message{Colors.RESET}\n")
                    return False
                
                # ✅ CORRECTION 3 : Chercher LE message avec le bon msg_id
                for msg in tester.received_messages[initial_count:]:
                    if "error" in msg:
                        # Erreur de parsing détectée
                        print(f"{Colors.RED}❌ ERREUR DE PARSING{Colors.RESET}")
                        print(f"{Colors.RED}   Type: {msg['error']}{Colors.RESET}")
                        print(f"{Colors.RED}   Exception: {msg.get('exception', 'N/A')}{Colors.RESET}")
                        if "raw_data" in msg:
                            print(f"{Colors.RED}   Données brutes (début): {msg['raw_data'][:200]}{Colors.RESET}")
                        print(f"{Colors.RED}🔴 PROBLÈME: PARSING - Le format JSON est cassé{Colors.RESET}\n")
                        return False
                    
                    if "data" in msg and msg["data"].get("msg_id") == test_id:
                        # ✅ CORRECTION 4 : Vérifier que le message est arrivé APRÈS l'envoi
                        if msg["timestamp"] < send_time:
                            print(f"{Colors.YELLOW}⚠ Message reçu AVANT l'envoi (message ancien en cache){Colors.RESET}")
                            continue
                        found_message = msg
                        break
                
                if found_message is None:
                    time.sleep(0.1)
            
            # ✅ CORRECTION 5 : Vérifier qu'il n'y a PAS de duplicata
            duplicates = []
            for msg in tester.received_messages[initial_count:]:
                if "data" in msg and msg["data"].get("msg_id") == test_id and msg != found_message:
                    duplicates.append(msg)
            
            if duplicates:
                print(f"{Colors.RED}❌ DUPLICATION: {len(duplicates)+1} messages avec msg_id={test_id}{Colors.RESET}")
                print(f"{Colors.RED}🔴 PROBLÈME: Le proxy duplique les messages{Colors.RESET}")
                print(f"\nMessages reçus avec msg_id={test_id}:")
                for i, msg in enumerate([found_message] + duplicates, 1):
                    print(f"   Message {i}: timestamp={msg['timestamp']}, size={msg['raw_size']} octets")
                print()
                return False
            
            print(f"{Colors.GREEN}✓ Message reçu ({found_message['raw_size']} octets){Colors.RESET}")
            print(f"{Colors.GREEN}✓ Aucun duplicata détecté{Colors.RESET}")
            
            # ✅ CORRECTION 6 : Comparaison détaillée
            print(f"🔍 Vérification de la correspondance (msg_id={test_id})...")
            error = compare_messages_detailed(found_message["data"], expected_msg)
            
            if error:
                print(f"\n{Colors.RED}{'=' * 80}{Colors.RESET}")
                print(f"{Colors.RED}❌ ÉCHEC DU TEST {test_id} ({format_size(size)}){Colors.RESET}")
                print(f"{Colors.RED}{'=' * 80}{Colors.RESET}")
                print(f"{Colors.RED}{error}{Colors.RESET}")
                print(f"{Colors.RED}{'=' * 80}{Colors.RESET}\n")
                return False
            
            print(f"{Colors.GREEN}✓✓✓ Message IDENTIQUE à celui envoyé!{Colors.RESET}")
            print(f"{Colors.GREEN}    msg_id={test_id} vérifié{Colors.RESET}")
            print(f"{Colors.GREEN}    Tous les champs correspondent{Colors.RESET}")
            print(f"{Colors.GREEN}    Payload vérifié byte par byte{Colors.RESET}")
            print(f"{Colors.GREEN}    Checksum valide{Colors.RESET}\n")
            
            # Petite pause entre les tests
            time.sleep(0.5)
        
        # Tous les tests sont passés
        print("=" * 80)
        print(f"{Colors.GREEN}✓✓✓ TOUS LES TESTS RÉUSSIS!{Colors.RESET}")
        print("=" * 80)
        print(f"{Colors.GREEN}Le proxy Redis fonctionne parfaitement jusqu'à 10 MB{Colors.RESET}")
        print(f"{Colors.GREEN}Aucun problème de découpage, couplage ou parsing détecté{Colors.RESET}")
        print("=" * 80)
        return True
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrompu par l'utilisateur{Colors.RESET}")
        return False
    except Exception as e:
        print(f"\n{Colors.RED}ERREUR FATALE: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        tester.stop()

if __name__ == "__main__":
    success = run_progressive_test()
    sys.exit(0 if success else 1)