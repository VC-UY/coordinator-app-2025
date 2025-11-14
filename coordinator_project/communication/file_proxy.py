"""
Proxy HTTP pour router les requêtes de fichiers entre Manager et Volontaire.
Le Coordinator agit comme un relais pour contourner les problèmes de NAT/sous-réseaux.
"""

import asyncio
import logging
import aiohttp
from aiohttp import web
import json
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)

class FileProxyServer:
    """
    Serveur proxy HTTP qui route les requêtes de fichiers.
    
    Architecture:
    - Manager demande: GET http://coordinator:8500/files/task_123/result.txt
    - Coordinator contacte: http://volunteer_ip:volunteer_port/files/result.txt
    - Coordinator retourne le fichier au Manager
    """
    
    def __init__(self, host='0.0.0.0', port=8500):
        self.host = host
        self.port = port
        self.app = None
        self.runner = None
        self.site = None
        
        # Registre des tâches: task_id -> (volunteer_ip, volunteer_port)
        self.task_registry: Dict[str, Dict] = {}
        
        # Statistiques
        self.stats = {
            'total_requests': 0,
            'successful_transfers': 0,
            'failed_transfers': 0,
            'bytes_transferred': 0,
            'start_time': time.time()
        }
    
    async def start(self):
        """Démarre le serveur proxy HTTP"""
        self.app = web.Application(
            client_max_size=100*1024*1024  # 100MB max par fichier
        )
        
        # Routes
        self.app.router.add_get('/files/{task_id}/{filename:.*}', self.handle_file_request)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/stats', self.handle_stats)
        self.app.router.add_post('/register_task', self.handle_register_task)
        self.app.router.add_delete('/unregister_task/{task_id}', self.handle_unregister_task)
        
        # Démarrer le serveur
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        logger.info(f"🚀 Proxy de fichiers démarré sur {self.host}:{self.port}")
        logger.info(f"📁 URL d'accès: http://{self.host}:{self.port}/files/<task_id>/<filename>")
    
    async def stop(self):
        """Arrête le serveur proxy"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Proxy de fichiers arrêté")
    
    def register_task(self, task_id: str, volunteer_ip: str, volunteer_port: int, volunteer_id: str = None):
        """
        Enregistre une tâche pour le routage de fichiers.
        
        Args:
            task_id: ID de la tâche
            volunteer_ip: IP du volontaire (vue par le coordinator)
            volunteer_port: Port du serveur de fichiers du volontaire
            volunteer_id: ID du volontaire (optionnel)
        """
        self.task_registry[task_id] = {
            'volunteer_ip': volunteer_ip,
            'volunteer_port': volunteer_port,
            'volunteer_id': volunteer_id,
            'registered_at': time.time()
        }
        logger.info(f"📝 Tâche {task_id} enregistrée: {volunteer_ip}:{volunteer_port}")
    
    def unregister_task(self, task_id: str):
        """Désenregistre une tâche"""
        if task_id in self.task_registry:
            del self.task_registry[task_id]
            logger.info(f"🗑️ Tâche {task_id} désenregistrée")
            return True
        return False
    
    async def handle_register_task(self, request):
        """
        Endpoint pour enregistrer une nouvelle tâche.
        POST /register_task
        Body: {"task_id": "...", "volunteer_ip": "...", "volunteer_port": ...}
        """
        try:
            data = await request.json()
            task_id = data.get('task_id')
            volunteer_ip = data.get('volunteer_ip')
            volunteer_port = data.get('volunteer_port')
            volunteer_id = data.get('volunteer_id')
            
            if not all([task_id, volunteer_ip, volunteer_port]):
                return web.json_response(
                    {'error': 'Missing required fields'},
                    status=400
                )
            
            self.register_task(task_id, volunteer_ip, volunteer_port, volunteer_id)
            
            return web.json_response({
                'status': 'success',
                'message': f'Task {task_id} registered',
                'proxy_url': f'http://{self.host}:{self.port}/files/{task_id}/'
            })
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de tâche: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def handle_unregister_task(self, request):
        """
        Endpoint pour désenregistrer une tâche.
        DELETE /unregister_task/<task_id>
        """
        task_id = request.match_info['task_id']
        
        if self.unregister_task(task_id):
            return web.json_response({
                'status': 'success',
                'message': f'Task {task_id} unregistered'
            })
        else:
            return web.json_response({
                'error': f'Task {task_id} not found'
            }, status=404)
    
    async def handle_file_request(self, request):
        """
        Gère une requête de fichier et la route vers le volontaire approprié.
        GET /files/<task_id>/<filename>
        """
        task_id = request.match_info['task_id']
        filename = request.match_info['filename']
        
        self.stats['total_requests'] += 1
        
        logger.info(f"📥 Requête de fichier: task={task_id}, file={filename}")
        
        # Vérifier si la tâche est enregistrée
        if task_id not in self.task_registry:
            logger.warning(f"❌ Tâche {task_id} non enregistrée")
            return web.json_response(
                {'error': f'Task {task_id} not registered'},
                status=404
            )
        
        task_info = self.task_registry[task_id]
        volunteer_ip = task_info['volunteer_ip']
        volunteer_port = task_info['volunteer_port']
        
        # Construire l'URL du volontaire
        volunteer_url = f"http://{volunteer_ip}:{volunteer_port}/files/{filename}"
        
        logger.info(f"🔄 Routage: {volunteer_url}")
        
        try:
            # Faire la requête au volontaire avec timeout
            timeout = aiohttp.ClientTimeout(total=60)  # 60 secondes
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(volunteer_url) as volunteer_response:
                    
                    if volunteer_response.status != 200:
                        logger.error(f"❌ Erreur du volontaire: {volunteer_response.status}")
                        self.stats['failed_transfers'] += 1
                        return web.Response(
                            status=volunteer_response.status,
                            text=f"Volunteer returned {volunteer_response.status}"
                        )
                    
                    # Lire le contenu du fichier
                    content = await volunteer_response.read()
                    
                    # Transférer les headers importants
                    headers = {}
                    if 'Content-Type' in volunteer_response.headers:
                        headers['Content-Type'] = volunteer_response.headers['Content-Type']
                    else:
                        headers['Content-Type'] = 'application/octet-stream'
                    
                    if 'Content-Length' in volunteer_response.headers:
                        headers['Content-Length'] = volunteer_response.headers['Content-Length']
                    
                    # Ajouter header custom pour indiquer le routage
                    headers['X-Routed-By'] = 'Coordinator-File-Proxy'
                    headers['X-Volunteer-Id'] = task_info.get('volunteer_id', 'unknown')
                    
                    # Mettre à jour les stats
                    self.stats['successful_transfers'] += 1
                    self.stats['bytes_transferred'] += len(content)
                    
                    logger.info(f"✅ Fichier transféré: {len(content)} bytes")
                    
                    # Retourner le fichier au manager
                    return web.Response(
                        body=content,
                        headers=headers,
                        status=200
                    )
        
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Timeout lors de la connexion au volontaire")
            self.stats['failed_transfers'] += 1
            return web.json_response(
                {'error': 'Timeout connecting to volunteer'},
                status=504
            )
        
        except aiohttp.ClientError as e:
            logger.error(f"❌ Erreur de connexion au volontaire: {e}")
            self.stats['failed_transfers'] += 1
            return web.json_response(
                {'error': f'Failed to connect to volunteer: {str(e)}'},
                status=502
            )
        
        except Exception as e:
            logger.error(f"❌ Erreur lors du routage de fichier: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.stats['failed_transfers'] += 1
            return web.json_response(
                {'error': f'Internal error: {str(e)}'},
                status=500
            )
    
    async def handle_health(self, request):
        """Endpoint de santé"""
        return web.json_response({
            'status': 'healthy',
            'uptime': time.time() - self.stats['start_time'],
            'registered_tasks': len(self.task_registry)
        })
    
    async def handle_stats(self, request):
        """Endpoint de statistiques"""
        return web.json_response({
            'stats': self.stats,
            'registered_tasks': len(self.task_registry),
            'tasks': list(self.task_registry.keys())
        })


# Instance singleton
_file_proxy_instance: Optional[FileProxyServer] = None

def get_file_proxy_instance(host='0.0.0.0', port=8000) -> FileProxyServer:
    """Récupère l'instance singleton du proxy de fichiers"""
    global _file_proxy_instance
    if _file_proxy_instance is None:
        _file_proxy_instance = FileProxyServer(host, port)
    return _file_proxy_instance


async def start_file_proxy_server(host='0.0.0.0', port=8000):
    """Démarre le serveur proxy de fichiers"""
    proxy = get_file_proxy_instance(host, port)
    await proxy.start()
    return proxy


# Pour démarrer en standalone
if __name__ == '__main__':
    async def main():
        proxy = await start_file_proxy_server()
        try:
            # Garder le serveur actif
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info("Arrêt du serveur...")
            await proxy.stop()
    
    asyncio.run(main())
