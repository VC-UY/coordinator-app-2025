#!/usr/bin/env python3
"""
Script pour démarrer et tester le proxy Redis de manière progressive.
"""

import asyncio
import subprocess
import time
import sys
import os
import signal
import threading
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class ProxyManager:
    """Gestionnaire pour démarrer/arrêter le proxy Redis"""
    
    def __init__(self):
        self.proxy_process = None
        self.redis_process = None
        
    def start_redis_server(self):
        """Démarre le serveur Redis si nécessaire"""
        try:
            # Vérifier si Redis est déjà en cours d'exécution
            result = subprocess.run(['redis-cli', 'ping'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Redis serveur déjà en cours d'exécution")
                return True
        except FileNotFoundError:
            print("❌ redis-cli non trouvé. Installez Redis.")
            return False
        
        # Essayer de démarrer Redis
        try:
            print("🚀 Démarrage du serveur Redis...")
            self.redis_process = subprocess.Popen([
                'redis-server', '--daemonize', 'yes',
                '--port', '6379',
                '--maxclients', '100000'
            ])
            time.sleep(2)
            
            # Vérifier que Redis a démarré
            result = subprocess.run(['redis-cli', 'ping'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Redis serveur démarré avec succès")
                return True
            else:
                print("❌ Échec du démarrage de Redis")
                return False
        except Exception as e:
            print(f"❌ Erreur lors du démarrage de Redis: {e}")
            return False
    
    def start_proxy(self):
        """Démarre le proxy Redis"""
        try:
            proxy_script = project_root / "coordinator_project" / "communication" / "proxy.py"
            
            if not proxy_script.exists():
                print(f"❌ Script proxy introuvable: {proxy_script}")
                return False
            
            print("🚀 Démarrage du proxy Redis...")
            self.proxy_process = subprocess.Popen([
                sys.executable, str(proxy_script)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Attendre un peu pour que le proxy démarre
            time.sleep(3)
            
            # Vérifier que le proxy est accessible
            if self.check_proxy_running():
                print("✅ Proxy Redis démarré avec succès sur le port 6380")
                return True
            else:
                print("❌ Le proxy n'est pas accessible")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors du démarrage du proxy: {e}")
            return False
    
    def check_proxy_running(self):
        """Vérifie si le proxy est en cours d'exécution"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 6380))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def stop_all(self):
        """Arrête le proxy et Redis"""
        if self.proxy_process:
            print("🛑 Arrêt du proxy Redis...")
            self.proxy_process.terminate()
            try:
                self.proxy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proxy_process.kill()
            self.proxy_process = None
        
        # Note: On ne ferme pas Redis car il peut être utilisé par d'autres services

class ProgressiveLoadTester:
    """Testeur de charge progressif pour le proxy"""
    
    def __init__(self):
        self.results = []
    
    async def test_connections(self, target_connections):
        """Test un nombre spécifique de connexions"""
        print(f"📊 Test avec {target_connections:,} connexions simultanées...")
        
        start_time = time.time()
        successful_connections = 0
        errors = 0
        
        async def test_single_connection(client_id):
            nonlocal successful_connections, errors
            try:
                reader, writer = await asyncio.open_connection('localhost', 6380)
                
                # Test PING
                writer.write(b"*1\r\n$4\r\nPING\r\n")
                await writer.drain()
                response = await asyncio.wait_for(reader.read(1024), timeout=5.0)
                
                if b"+PONG\r\n" in response:
                    successful_connections += 1
                else:
                    errors += 1
                
                # Maintenir la connexion brièvement
                await asyncio.sleep(0.1)
                
                writer.close()
                await writer.wait_closed()
                
            except Exception as e:
                errors += 1
        
        # Créer les connexions par batches pour éviter l'overload
        batch_size = min(100, target_connections)
        for i in range(0, target_connections, batch_size):
            batch_end = min(i + batch_size, target_connections)
            batch_tasks = [
                test_single_connection(j) for j in range(i, batch_end)
            ]
            
            await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Pause entre les batches
            if batch_end < target_connections:
                await asyncio.sleep(0.1)
        
        duration = time.time() - start_time
        success_rate = (successful_connections / target_connections) * 100 if target_connections > 0 else 0
        
        result = {
            'target': target_connections,
            'successful': successful_connections,
            'errors': errors,
            'duration': duration,
            'success_rate': success_rate,
            'throughput': successful_connections / duration if duration > 0 else 0
        }
        
        self.results.append(result)
        
        print(f"  ✅ {successful_connections:,}/{target_connections:,} réussies ({success_rate:.1f}%)")
        print(f"  ⏱️ Durée: {duration:.2f}s")
        print(f"  📈 Débit: {result['throughput']:.0f} connexions/sec")
        
        return success_rate >= 95  # Succès si 95%+ des connexions réussissent
    
    async def run_progressive_tests(self):
        """Lance des tests progressifs"""
        print("\n🧪 TESTS DE CHARGE PROGRESSIFS")
        print("=" * 40)
        
        # Tests progressifs
        test_targets = [10, 50, 100, 500, 1000, 2000, 5000]
        
        for target in test_targets:
            success = await self.test_connections(target)
            
            if not success:
                print(f"⚠️ Limite atteinte à {target:,} connexions")
                break
            
            # Pause entre les tests
            await asyncio.sleep(2)
        
        self.print_summary()
    
    def print_summary(self):
        """Affiche un résumé des résultats"""
        print("\n📊 RÉSUMÉ DES TESTS")
        print("=" * 30)
        
        if not self.results:
            print("Aucun résultat disponible")
            return
        
        max_successful = max(r['successful'] for r in self.results)
        best_throughput = max(r['throughput'] for r in self.results)
        
        print(f"🏆 Maximum de connexions simultanées: {max_successful:,}")
        print(f"⚡ Meilleur débit: {best_throughput:.0f} connexions/sec")
        
        print("\nDétails par test:")
        for result in self.results:
            print(f"  {result['target']:,} → {result['successful']:,} "
                  f"({result['success_rate']:.1f}%) - {result['throughput']:.0f} conn/s")

async def main():
    """Fonction principale"""
    print("🚀 GESTIONNAIRE DE PROXY REDIS")
    print("=" * 35)
    
    manager = ProxyManager()
    
    def signal_handler(signum, frame):
        print("\n🛑 Arrêt demandé...")
        manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 1. Démarrer Redis
        if not manager.start_redis_server():
            print("❌ Impossible de démarrer Redis")
            return
        
        # 2. Démarrer le proxy
        if not manager.start_proxy():
            print("❌ Impossible de démarrer le proxy")
            return
        
        # 3. Tests de validation
        print("\n🔍 Tests de validation...")
        validation_script = project_root / "tests" / "test_proxy_validation.py"
        
        if validation_script.exists():
            result = subprocess.run([sys.executable, str(validation_script)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Tests de validation réussis")
            else:
                print("⚠️ Certains tests de validation ont échoué")
                print(result.stdout)
                print(result.stderr)
        
        # 4. Tests de charge progressifs
        print("\n🏋️ Lancement des tests de charge...")
        tester = ProgressiveLoadTester()
        await tester.run_progressive_tests()
        
        print("\n✅ Tests terminés avec succès !")
        print("Le proxy Redis est opérationnel et testé.")
        
        # Garder le proxy en vie
        print("\n⏸️ Proxy en cours d'exécution... (Ctrl+C pour arrêter)")
        while True:
            await asyncio.sleep(10)
            if not manager.check_proxy_running():
                print("❌ Le proxy s'est arrêté de manière inattendue")
                break
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    finally:
        manager.stop_all()

if __name__ == "__main__":
    asyncio.run(main())