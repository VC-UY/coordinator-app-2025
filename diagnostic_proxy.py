#!/usr/bin/env python3
"""
Test de diagnostic simple pour le proxy Redis
"""
import socket
import time

def test_basic_tcp_connection():
    """Test de connexion TCP basique au proxy"""
    print("🔍 Test de connexion TCP basique au proxy...")
    
    try:
        # Création d'une socket TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        # Connexion au proxy
        print("📡 Connexion au proxy sur localhost:6380...")
        sock.connect(('localhost', 6380))
        print("✅ Connexion établie")
        
        # Envoyer une commande PING simple
        print("📤 Envoi de la commande PING...")
        ping_command = b"*1\r\n$4\r\nPING\r\n"
        sock.send(ping_command)
        
        # Attendre la réponse
        print("📥 Attente de la réponse...")
        response = sock.recv(1024)
        print(f"📨 Réponse reçue: {response}")
        
        # Vérifier si c'est PONG
        if b"+PONG\r\n" in response:
            print("✅ PING/PONG réussi !")
            return True
        else:
            print(f"❌ Réponse inattendue: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass

def test_redis_direct():
    """Test de connexion directe à Redis"""
    print("\n🔍 Test de connexion directe à Redis...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        print("📡 Connexion directe à Redis sur localhost:6379...")
        sock.connect(('localhost', 6379))
        print("✅ Connexion établie")
        
        # Envoyer PING à Redis
        ping_command = b"*1\r\n$4\r\nPING\r\n"
        sock.send(ping_command)
        
        response = sock.recv(1024)
        print(f"📨 Réponse Redis: {response}")
        
        if b"+PONG\r\n" in response:
            print("✅ Redis fonctionne correctement !")
            return True
        else:
            print(f"❌ Redis problème: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur Redis: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass

if __name__ == "__main__":
    print("🚀 DIAGNOSTIC DU PROXY REDIS")
    print("=" * 30)
    
    # Test Redis direct
    redis_ok = test_redis_direct()
    
    # Test proxy
    proxy_ok = test_basic_tcp_connection()
    
    print("\n📊 RÉSUMÉ")
    print("=" * 15)
    print(f"Redis direct: {'✅' if redis_ok else '❌'}")
    print(f"Proxy Redis:  {'✅' if proxy_ok else '❌'}")
    
    if redis_ok and not proxy_ok:
        print("\n💡 DIAGNOSTIC:")
        print("- Redis fonctionne correctement")
        print("- Le proxy a un problème de communication")
        print("- Vérifiez les logs du proxy")
        print("- Le proxy pourrait ne pas être compatible avec cette version de Redis")