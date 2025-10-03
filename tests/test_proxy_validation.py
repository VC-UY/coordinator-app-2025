#!/usr/bin/env python3
"""
Tests de validation pour le proxy Redis.
Vérifie le bon fonctionnement de base avant les tests de performance.
"""

import asyncio
import time
import json
import logging
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import redis

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ProxyValidation')

class ProxyValidationTests:
    """Tests de validation du proxy Redis"""
    
    def __init__(self, proxy_host='localhost', proxy_port=6380, redis_host='localhost', redis_port=6379):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.redis_host = redis_host
        self.redis_port = redis_port
        
        # Client Redis direct pour comparaison
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        self.test_results = {}
    
    async def run_all_tests(self):
        """Exécute tous les tests de validation"""
        print("🔍 TESTS DE VALIDATION DU PROXY REDIS")
        print("=" * 50)
        
        tests = [
            self.test_basic_connection,
            self.test_ping_command,
            self.test_basic_publish_subscribe,
            self.test_authentication,
            self.test_multiple_clients,
            self.test_redis_commands,
            self.test_error_handling,
            self.test_connection_cleanup
        ]
        
        total_tests = len(tests)
        passed_tests = 0
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed_tests += 1
                    print(f"✅ {test.__name__}")
                else:
                    print(f"❌ {test.__name__}")
            except Exception as e:
                print(f"❌ {test.__name__} - Erreur: {e}")
                logger.error(f"Erreur dans {test.__name__}: {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 RÉSULTATS: {passed_tests}/{total_tests} tests réussis")
        
        if passed_tests == total_tests:
            print("🎉 Tous les tests sont passés ! Le proxy est prêt pour les tests de performance.")
        else:
            print("⚠️  Certains tests ont échoué. Vérifiez la configuration du proxy.")
        
        return passed_tests == total_tests
    
    async def test_basic_connection(self):
        """Test de connexion de base au proxy"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.proxy_host, self.proxy_port),
                timeout=5.0
            )
            
            writer.close()
            await writer.wait_closed()
            return True
        except Exception as e:
            logger.error(f"Échec connexion de base: {e}")
            return False
    
    async def test_ping_command(self):
        """Test de la commande PING"""
        try:
            reader, writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)
            
            # Envoyer PING
            ping_cmd = b"*1\r\n$4\r\nPING\r\n"
            writer.write(ping_cmd)
            await writer.drain()
            
            # Lire la réponse
            response = await asyncio.wait_for(reader.read(1024), timeout=5.0)
            
            writer.close()
            await writer.wait_closed()
            
            # Vérifier la réponse PONG
            return b"+PONG\r\n" in response
        except Exception as e:
            logger.error(f"Échec test PING: {e}")
            return False
    
    async def test_basic_publish_subscribe(self):
        """Test de base publish/subscribe"""
        try:
            # Client subscriber
            reader1, writer1 = await asyncio.open_connection(self.proxy_host, self.proxy_port)
            
            # Client publisher
            reader2, writer2 = await asyncio.open_connection(self.proxy_host, self.proxy_port)
            
            # S'abonner à un canal
            subscribe_cmd = b"*2\r\n$9\r\nSUBSCRIBE\r\n$12\r\ntest/channel\r\n"
            writer1.write(subscribe_cmd)
            await writer1.drain()
            
            # Lire la confirmation de souscription
            sub_response = await reader1.read(1024)
            
            # Publier un message
            test_message = "Hello World!"
            channel = "test/channel"
            publish_cmd = f"*3\r\n$7\r\nPUBLISH\r\n${len(channel)}\r\n{channel}\r\n${len(test_message)}\r\n{test_message}\r\n"
            writer2.write(publish_cmd.encode())
            await writer2.drain()
            
            # Lire la réponse du publish
            pub_response = await reader2.read(1024)
            
            # Lire le message publié
            message_response = await asyncio.wait_for(reader1.read(1024), timeout=5.0)
            
            # Fermer les connexions
            writer1.close()
            writer2.close()
            await writer1.wait_closed()
            await writer2.wait_closed()
            
            # Vérifier que le message a été reçu
            return test_message.encode() in message_response
        except Exception as e:
            logger.error(f"Échec test pub/sub: {e}")
            return False
    
    async def test_authentication(self):
        """Test du système d'authentification"""
        try:
            reader, writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)
            
            # Test AUTH avec un token simple
            auth_cmd = b"*2\r\n$4\r\nAUTH\r\n$10\r\ntest_token\r\n"
            writer.write(auth_cmd)
            await writer.drain()
            
            response = await reader.read(1024)
            
            writer.close()
            await writer.wait_closed()
            
            # Vérifier que l'authentification est acceptée
            return b"+OK\r\n" in response
        except Exception as e:
            logger.error(f"Échec test authentification: {e}")
            return False
    
    async def test_multiple_clients(self):
        """Test avec plusieurs clients simultanés"""
        try:
            async def test_client(client_id):
                reader, writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)
                
                # PING
                ping_cmd = b"*1\r\n$4\r\nPING\r\n"
                writer.write(ping_cmd)
                await writer.drain()
                response = await reader.read(1024)
                
                writer.close()
                await writer.wait_closed()
                
                return b"+PONG\r\n" in response
            
            # Tester 10 clients simultanés
            tasks = [test_client(i) for i in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Vérifier que tous les clients ont réussi
            success_count = sum(1 for result in results if result is True)
            return success_count == 10
        except Exception as e:
            logger.error(f"Échec test clients multiples: {e}")
            return False
    
    async def test_redis_commands(self):
        """Test de commandes Redis diverses"""
        try:
            reader, writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)
            
            # Test SET
            set_cmd = b"*3\r\n$3\r\nSET\r\n$8\r\ntest_key\r\n$10\r\ntest_value\r\n"
            writer.write(set_cmd)
            await writer.drain()
            set_response = await reader.read(1024)
            
            # Test GET
            get_cmd = b"*2\r\n$3\r\nGET\r\n$8\r\ntest_key\r\n"
            writer.write(get_cmd)
            await writer.drain()
            get_response = await reader.read(1024)
            
            writer.close()
            await writer.wait_closed()
            
            # Vérifier les réponses
            return b"+OK\r\n" in set_response and b"test_value" in get_response
        except Exception as e:
            logger.error(f"Échec test commandes Redis: {e}")
            return False
    
    async def test_error_handling(self):
        """Test de la gestion d'erreurs"""
        try:
            reader, writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)
            
            # Envoyer une commande invalide
            invalid_cmd = b"*1\r\n$7\r\nINVALID\r\n"
            writer.write(invalid_cmd)
            await writer.drain()
            
            response = await reader.read(1024)
            
            writer.close()
            await writer.wait_closed()
            
            # Vérifier qu'une erreur est retournée
            return b"-ERR" in response
        except Exception as e:
            logger.error(f"Échec test gestion erreurs: {e}")
            return False
    
    async def test_connection_cleanup(self):
        """Test du nettoyage des connexions"""
        try:
            # Créer et fermer brutalement des connexions
            for _ in range(5):
                reader, writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)
                # Fermer brutalement sans attendre
                writer.close()
            
            # Attendre un peu pour le nettoyage
            await asyncio.sleep(1)
            
            # Vérifier qu'on peut encore se connecter
            reader, writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)
            writer.close()
            await writer.wait_closed()
            
            return True
        except Exception as e:
            logger.error(f"Échec test nettoyage connexions: {e}")
            return False
    
    def check_redis_server(self):
        """Vérifie que le serveur Redis est accessible"""
        try:
            self.redis_client.ping()
            print(f"✅ Redis serveur accessible sur {self.redis_host}:{self.redis_port}")
            return True
        except Exception as e:
            print(f"❌ Redis serveur inaccessible: {e}")
            return False
    
    def check_proxy_server(self):
        """Vérifie que le proxy est démarré"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.proxy_host, self.proxy_port))
            sock.close()
            
            if result == 0:
                print(f"✅ Proxy Redis accessible sur {self.proxy_host}:{self.proxy_port}")
                return True
            else:
                print(f"❌ Proxy Redis inaccessible sur {self.proxy_host}:{self.proxy_port}")
                return False
        except Exception as e:
            print(f"❌ Erreur lors de la vérification du proxy: {e}")
            return False

async def main():
    """Fonction principale pour lancer les tests de validation"""
    print("🚀 VALIDATION DU PROXY REDIS")
    print("=" * 30)
    
    tester = ProxyValidationTests()
    
    # Vérifications préliminaires
    print("🔧 Vérifications préliminaires...")
    redis_ok = tester.check_redis_server()
    proxy_ok = tester.check_proxy_server()
    
    if not redis_ok:
        print("❌ Démarrez Redis avant de lancer les tests")
        print("   sudo systemctl start redis")
        return False
    
    if not proxy_ok:
        print("❌ Démarrez le proxy Redis avant de lancer les tests")
        print("   cd coordinator_project && python manage.py start_redis_proxy")
        return False
    
    print("\n🧪 Lancement des tests de validation...")
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎯 Le proxy est prêt pour les tests de performance !")
        print("   Vous pouvez maintenant lancer les tests de charge.")
    else:
        print("\n❌ Corrigez les problèmes avant de continuer.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())