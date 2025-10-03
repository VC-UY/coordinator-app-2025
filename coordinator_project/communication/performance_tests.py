"""
Tests de performance pour le proxy Redis optimisé
Teste jusqu'à 100K connexions simultanées
"""

import asyncio
import time
import json
import logging
import statistics
from typing import List, Dict
import psutil
import threading
from dataclasses import dataclass
from redis import asyncio as redis 

@dataclass
class TestResult:
    test_name: str
    duration: float
    success_count: int
    error_count: int
    avg_latency: float
    p99_latency: float
    throughput: float
    memory_usage: float
    cpu_usage: float

class ProxyLoadTester:
    """Testeur de charge pour le proxy Redis optimisé"""
    
    def __init__(self, proxy_host='localhost', proxy_port=6380):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.results = []
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('LoadTester')
    
    async def test_concurrent_connections(self, target_clients: int) -> TestResult:
        """Test les connexions simultanées"""
        self.logger.info(f"Test connexions: {target_clients:,} clients")
        
        start_time = time.time()
        memory_start = psutil.Process().memory_info().rss / 1024 / 1024
        
        successful_connections = 0
        errors = 0
        latencies = []
        
        async def create_connection(client_id):
            nonlocal successful_connections, errors
            try:
                conn_start = time.time()
                reader, writer = await asyncio.open_connection(
                    self.proxy_host, self.proxy_port
                )
                conn_time = (time.time() - conn_start) * 1000
                latencies.append(conn_time)
                
                # Test PING
                writer.write(b"*1\r\n$4\r\nPING\r\n")
                await writer.drain()
                response = await reader.read(1024)
                
                successful_connections += 1
                
                # Maintenir la connexion brièvement
                await asyncio.sleep(2)
                
                writer.close()
                await writer.wait_closed()
                
            except Exception as e:
                errors += 1
                self.logger.debug(f"Erreur client {client_id}: {e}")
        
        # Créer les connexions par batches
        batch_size = min(1000, target_clients)
        for i in range(0, target_clients, batch_size):
            batch_end = min(i + batch_size, target_clients)
            batch_tasks = [
                create_connection(j) for j in range(i, batch_end)
            ]
            
            await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Pause entre batches
            if batch_end < target_clients:
                await asyncio.sleep(0.1)
        
        duration = time.time() - start_time
        memory_end = psutil.Process().memory_info().rss / 1024 / 1024
        memory_usage = memory_end - memory_start
        
        # Calculer les métriques
        avg_latency = statistics.mean(latencies) if latencies else 0
        p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else avg_latency
        
        result = TestResult(
            test_name=f"connections_{target_clients}",
            duration=duration,
            success_count=successful_connections,
            error_count=errors,
            avg_latency=avg_latency,
            p99_latency=p99_latency,
            throughput=successful_connections / duration,
            memory_usage=memory_usage,
            cpu_usage=psutil.cpu_percent()
        )
        
        success_rate = successful_connections / target_clients * 100
        self.logger.info(f"  ✅ {successful_connections:,}/{target_clients:,} connexions ({success_rate:.1f}%)")
        self.logger.info(f"  ⏱️ Latence P99: {p99_latency:.2f}ms")
        
        return result
    
    async def test_pub_sub_performance(self, subscribers: int, publishers: int) -> TestResult:
        """Test les performances pub/sub"""
        self.logger.info(f"Test pub/sub: {subscribers:,} subscribers, {publishers:,} publishers")
        
        start_time = time.time()
        messages_received = 0
        messages_published = 0
        errors = 0
        
        # Variables partagées pour synchronisation
        test_duration = 30  # durée du test en secondes
        stop_event = asyncio.Event()
        
        async def reader(channel: redis.client.PubSub):
            nonlocal messages_received
            try:
                while not stop_event.is_set():
                    try:
                        message = await asyncio.wait_for(
                            channel.get_message(ignore_subscribe_messages=True, timeout=1.0),
                            timeout=2.0
                        )
                        if message is not None:
                            messages_received += 1
                            self.logger.debug(f"(Reader) Message Received: {message}")
                            
                            # Vérifier si c'est un message STOP
                            if isinstance(message.get('data'), bytes):
                                try:
                                    data = json.loads(message['data'].decode())
                                    if data.get('type') == 'STOP':
                                        self.logger.info("(Reader) STOP signal received")
                                        break
                                except (json.JSONDecodeError, AttributeError):
                                    # Message normal, continuer
                                    pass
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        self.logger.debug(f"Erreur dans reader: {e}")
                        break
            except Exception as e:
                self.logger.error(f"Erreur générale dans reader: {e}")

        async def publisher_client(client_id):
            nonlocal messages_published, errors
            try:
                reader, writer = await asyncio.open_connection(
                    self.proxy_host, self.proxy_port
                )
                
                # Publier des messages pendant la durée du test
                end_time = time.time() + test_duration
                msg_count = 0
                
                while time.time() < end_time and not stop_event.is_set():
                    message = json.dumps({
                        'data': f"Message test number {msg_count} from client {client_id}",
                        'publisher_id': client_id,
                        'message_id': msg_count,
                        'timestamp': time.time(),
                        'type': 'normal'
                    })
                    
                    # Commande PUBLISH Redis
                    channel = 'test/channel'
                    command = f"*3\r\n$7\r\nPUBLISH\r\n${len(channel)}\r\n{channel}\r\n${len(message)}\r\n{message}\r\n"
                    
                    writer.write(command.encode())
                    await writer.drain()
                    
                    # Lire la réponse
                    response = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                    if response:
                        messages_published += 1
                        self.logger.debug(f"Publisher {client_id} sent message {msg_count}")
                    else:
                        errors += 1
                        self.logger.error(f"Publisher {client_id} failed to send message {msg_count}")
                    
                    msg_count += 1
                    await asyncio.sleep(0.1)  # 10 messages/sec
                
                # Envoyer signal STOP à la fin
                if client_id == 0:  # Seul le premier publisher envoie le STOP
                    stop_message = json.dumps({
                        'type': 'STOP',
                        'publisher_id': client_id,
                        'timestamp': time.time()
                    })
                    channel = 'test/channel'
                    command = f"*3\r\n$7\r\nPUBLISH\r\n${len(channel)}\r\n{channel}\r\n${len(stop_message)}\r\n{stop_message}\r\n"
                    writer.write(command.encode())
                    await writer.drain()
                    await reader.read(1024)
                
                writer.close()
                await writer.wait_closed()
                
            except Exception as e:
                errors += 1
                self.logger.debug(f"Erreur publisher {client_id}: {e}")

        # Démarrer les subscribers et publishers
        try:
            r = redis.from_url(f"redis://{self.proxy_host}:{self.proxy_port}")
            async with r.pubsub() as pubsub:
                await pubsub.subscribe("test/channel")
                
                # Créer les tâches subscriber
                subscriber_tasks = [
                    asyncio.create_task(reader(pubsub)) for i in range(subscribers)
                ]
                
                # Attendre que les subscribers se connectent
                await asyncio.sleep(2)
                
                # Créer les tâches publisher
                publisher_tasks = [
                    asyncio.create_task(publisher_client(i)) for i in range(publishers)
                ]
                
                # Attendre que tous les publishers terminent
                await asyncio.gather(*publisher_tasks, return_exceptions=True)
                
                # Donner un peu de temps pour que les derniers messages soient reçus
                await asyncio.sleep(2)
                
                # Arrêter les subscribers
                stop_event.set()
                
                # Attendre que les subscribers se terminent (avec timeout)
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*subscriber_tasks, return_exceptions=True),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    self.logger.warning("Timeout lors de l'arrêt des subscribers")
                    
        except Exception as e:
            self.logger.error(f"Erreur dans test_pub_sub_performance: {e}")
            errors += 1
        finally:
            duration = time.time() - start_time
            
            # Calculer les statistiques finales
            result = TestResult(
                test_name=f"pubsub_{subscribers}sub_{publishers}pub",
                duration=duration,
                success_count=messages_received,
                error_count=errors,
                avg_latency=0,
                p99_latency=0,
                throughput=messages_received / duration if duration > 0 else 0,
                memory_usage=psutil.Process().memory_info().rss / 1024 / 1024,
                cpu_usage=psutil.cpu_percent()
            )
            
            self.logger.info(f"  📨 {messages_received:,} messages reçus")
            self.logger.info(f"  📤 {messages_published:,} messages publiés") 
            self.logger.info(f"  📈 Débit: {result.throughput:.0f} msg/s")
            self.logger.info(f"  ⏱️ Durée: {duration:.2f}s")
            
            return result
    
    async def test_stress_limit(self) -> List[TestResult]:
        """Test de stress pour trouver la limite"""
        self.logger.info("Test de stress - recherche de la limite")
        
        results = []
        client_counts = [1000, 5000, 10000, 25000, 50000, 75000, 100000]
        
        for client_count in client_counts:
            try:
                result = await self.test_concurrent_connections(client_count)
                results.append(result)
                
                success_rate = result.success_count / client_count * 100
                
                # Arrêter si le taux de succès devient trop faible
                if success_rate < 80:
                    self.logger.warning(f"Limite atteinte à {client_count:,} clients ({success_rate:.1f}% succès)")
                    break
                
                # Pause entre les tests
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Erreur test stress {client_count}: {e}")
                break
        
        return results
    
    async def run_full_test_suite(self):
        """Exécute la suite complète de tests"""
        self.logger.info("🚀 Démarrage des tests de performance")
        
        all_results = {}
        
        # Test 1: Connexions croissantes
        self.logger.info("\n📊 Test 1: Connexions simultanées")
        connection_tests = [1000, 5000, 10000, 25000, 50000]
        # connection_tests = [ 50000]
        all_results['connections'] = []
        
        for count in connection_tests:
            try:
                result = await self.test_concurrent_connections(count)
                all_results['connections'].append(result)
                await asyncio.sleep(2)
            except Exception as e:
                self.logger.error(f"Erreur test connexions {count}: {e}")
        
        # Test 2: Pub/Sub
        self.logger.info("\n📬 Test 2: Performance Pub/Sub")
        pubsub_configs = [
            (1000, 10),
            (5000, 50),
            (10000, 100)
        ]
        all_results['pubsub'] = []
        
        for subscribers, publishers in pubsub_configs:
            try:
                result = await self.test_pub_sub_performance(subscribers, publishers)
                all_results['pubsub'].append(result)
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"Erreur test pubsub {subscribers}/{publishers}: {e}")
        
        # Test 3: Stress
        self.logger.info("\n🔥 Test 3: Test de stress")
        try:
            stress_results = await self.test_stress_limit()
            all_results['stress'] = stress_results
        except Exception as e:
            self.logger.error(f"Erreur test stress: {e}")
            all_results['stress'] = []
        
        # Générer le rapport
        self.generate_report(all_results)
        
        return all_results
    
    def generate_report(self, results: Dict[str, List[TestResult]]):
        """Génère un rapport de performance"""
        print("\n" + "="*80)
        print("📊 RAPPORT DE PERFORMANCE - PROXY REDIS OPTIMISÉ")
        print("="*80)
        
        for test_type, test_results in results.items():
            print(f"\n🔍 {test_type.upper()}")
            print("-" * 50)
            
            for result in test_results:
                success_rate = result.success_count / (result.success_count + result.error_count) * 100
                
                print(f"Test: {result.test_name}")
                print(f"  ✅ Succès: {result.success_count:,} ({success_rate:.1f}%)")
                print(f"  ❌ Erreurs: {result.error_count:,}")
                print(f"  ⏱️  Durée: {result.duration:.2f}s")
                print(f"  📈 Débit: {result.throughput:.0f} ops/s")
                if result.avg_latency > 0:
                    print(f"  🕐 Latence moy: {result.avg_latency:.2f}ms")
                    print(f"  🕐 P99: {result.p99_latency:.2f}ms")
                print(f"  💾 RAM: +{result.memory_usage:.1f}MB")
                print(f"  🖥️  CPU: {result.cpu_usage:.1f}%")
                print()
        
        # Résumé des capacités
        print("\n🎯 RÉSUMÉ DES CAPACITÉS")
        print("-" * 30)
        
        if 'stress' in results and results['stress']:
            max_clients = max(r.success_count for r in results['stress'])
            print(f"📊 Clients simultanés max: {max_clients:,}")
        
        if 'pubsub' in results and results['pubsub']:
            max_throughput = max(r.throughput for r in results['pubsub'])
            print(f"📨 Débit max pub/sub: {max_throughput:.0f} msg/s")
        
        if 'connections' in results and results['connections']:
            avg_latency = statistics.mean(r.avg_latency for r in results['connections'] if r.avg_latency > 0)
            print(f"🕐 Latence moyenne: {avg_latency:.2f}ms")

async def main():
    """Fonction principale pour lancer les tests"""
    tester = ProxyLoadTester()
    await tester.run_full_test_suite()

if __name__ == "__main__":
    asyncio.run(main())