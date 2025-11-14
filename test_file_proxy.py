#!/usr/bin/env python3
"""
Script de test pour le proxy de fichiers.
Simule un volontaire, un coordinator et un manager.
"""

import asyncio
import aiohttp
from aiohttp import web
import logging
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'coordinator_project'))

from communication.file_proxy import FileProxyServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Serveur de fichiers du "volontaire" simulé
class MockVolunteerFileServer:
    def __init__(self, port=9000):
        self.port = port
        self.app = None
        self.runner = None
        
    async def start(self):
        self.app = web.Application()
        self.app.router.add_get('/files/{filename}', self.handle_file)
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '127.0.0.1', self.port)
        await site.start()
        logger.info(f"🎭 Mock Volunteer File Server démarré sur le port {self.port}")
    
    async def handle_file(self, request):
        filename = request.match_info['filename']
        logger.info(f"📥 Volontaire: Requête de fichier {filename}")
        
        # Simuler un fichier
        content = f"Contenu du fichier {filename} généré par le volontaire\n"
        content += "Ceci est un test du proxy de fichiers.\n"
        content += "Le coordinator route cette requête depuis le manager.\n"
        
        return web.Response(
            text=content,
            headers={'Content-Type': 'text/plain'}
        )
    
    async def stop(self):
        if self.runner:
            await self.runner.cleanup()

async def test_file_proxy():
    """Test complet du proxy de fichiers"""
    
    print("\n" + "="*60)
    print("TEST DU PROXY DE FICHIERS")
    print("="*60 + "\n")
    
    # 1. Démarrer le serveur de fichiers du volontaire (simulé)
    print("1️⃣ Démarrage du serveur de fichiers du volontaire...")
    volunteer_server = MockVolunteerFileServer(port=9000)
    await volunteer_server.start()
    
    # 2. Démarrer le proxy de fichiers du coordinator
    print("\n2️⃣ Démarrage du proxy de fichiers du coordinator...")
    file_proxy = FileProxyServer(host='127.0.0.1', port=8000)
    await file_proxy.start()
    
    await asyncio.sleep(1)  # Laisser les serveurs démarrer
    
    # 3. Enregistrer une tâche dans le proxy
    print("\n3️⃣ Enregistrement de la tâche dans le proxy...")
    task_id = "test_task_123"
    volunteer_ip = "127.0.0.1"
    volunteer_port = 9000
    
    file_proxy.register_task(
        task_id=task_id,
        volunteer_ip=volunteer_ip,
        volunteer_port=volunteer_port,
        volunteer_id="volunteer_test"
    )
    
    print(f"   ✅ Tâche {task_id} enregistrée")
    print(f"   📍 Volontaire: {volunteer_ip}:{volunteer_port}")
    print(f"   🔗 URL du proxy: http://127.0.0.1:8000/files/{task_id}/")
    
    # 4. Simuler le manager qui télécharge un fichier
    print("\n4️⃣ Simulation du manager téléchargeant un fichier...")
    
    filename = "result.txt"
    proxy_url = f"http://127.0.0.1:8000/files/{task_id}/{filename}"
    
    print(f"   📥 Manager demande: {proxy_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(proxy_url) as response:
                if response.status == 200:
                    content = await response.text()
                    print(f"   ✅ Fichier reçu avec succès!")
                    print(f"\n   📄 Contenu du fichier:")
                    print("   " + "-"*50)
                    for line in content.split('\n'):
                        print(f"   {line}")
                    print("   " + "-"*50)
                    
                    # Vérifier les headers
                    routed_by = response.headers.get('X-Routed-By')
                    volunteer_id = response.headers.get('X-Volunteer-Id')
                    print(f"\n   🏷️ Headers:")
                    print(f"      X-Routed-By: {routed_by}")
                    print(f"      X-Volunteer-Id: {volunteer_id}")
                else:
                    print(f"   ❌ Erreur: Status {response.status}")
                    print(f"   {await response.text()}")
    except Exception as e:
        print(f"   ❌ Erreur lors du téléchargement: {e}")
    
    # 5. Vérifier les statistiques
    print("\n5️⃣ Vérification des statistiques...")
    
    stats_url = "http://127.0.0.1:8000/stats"
    async with aiohttp.ClientSession() as session:
        async with session.get(stats_url) as response:
            if response.status == 200:
                stats = await response.json()
                print(f"   📊 Statistiques du proxy:")
                print(f"      Total requêtes: {stats['stats']['total_requests']}")
                print(f"      Transferts réussis: {stats['stats']['successful_transfers']}")
                print(f"      Transferts échoués: {stats['stats']['failed_transfers']}")
                print(f"      Bytes transférés: {stats['stats']['bytes_transferred']}")
                print(f"      Tâches enregistrées: {stats['registered_tasks']}")
    
    # 6. Test de santé
    print("\n6️⃣ Test de santé du proxy...")
    
    health_url = "http://127.0.0.1:8000/health"
    async with aiohttp.ClientSession() as session:
        async with session.get(health_url) as response:
            if response.status == 200:
                health = await response.json()
                print(f"   ✅ Proxy en bonne santé")
                print(f"      Status: {health['status']}")
                print(f"      Uptime: {health['uptime']:.2f}s")
    
    # 7. Désenregistrer la tâche
    print("\n7️⃣ Désenregistrement de la tâche...")
    
    unregister_url = f"http://127.0.0.1:8000/unregister_task/{task_id}"
    async with aiohttp.ClientSession() as session:
        async with session.delete(unregister_url) as response:
            if response.status == 200:
                print(f"   ✅ Tâche {task_id} désenregistrée")
    
    # 8. Vérifier que la tâche n'est plus accessible
    print("\n8️⃣ Vérification que la tâche n'est plus accessible...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(proxy_url) as response:
            if response.status == 404:
                print(f"   ✅ Tâche correctement désenregistrée (404 Not Found)")
            else:
                print(f"   ❌ Erreur: la tâche est toujours accessible")
    
    # Nettoyage
    print("\n9️⃣ Nettoyage...")
    await file_proxy.stop()
    await volunteer_server.stop()
    
    print("\n" + "="*60)
    print("✅ TEST TERMINÉ AVEC SUCCÈS")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        asyncio.run(test_file_proxy())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrompu par l'utilisateur")
