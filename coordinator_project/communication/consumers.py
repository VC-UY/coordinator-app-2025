import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskUpdatesConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour les mises à jour en temps réel des tâches et workflows.
    Les clients se connectent à ws://localhost:8001/ws/tasks/ pour recevoir les updates.
    """

    async def connect(self):
        """Appelé quand un client WebSocket se connecte"""
        # Ajouter ce consumer au groupe "tasks_updates"
        self.group_name = 'tasks_updates'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connecté: {self.channel_name}")

        # Envoyer un message de bienvenue
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connecté au système de mises à jour en temps réel',
            'timestamp': datetime.now().isoformat()
        }))

    async def disconnect(self, close_code):
        """Appelé quand un client WebSocket se déconnecte"""
        # Retirer ce consumer du groupe
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket déconnecté: {self.channel_name} (code: {close_code})")

    async def receive(self, text_data):
        """
        Appelé quand le serveur reçoit un message du client.
        Le client peut s'abonner à des types spécifiques d'événements.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'subscribe':
                # Le client s'abonne à des types spécifiques
                subscriptions = data.get('topics', [])
                await self.send(text_data=json.dumps({
                    'type': 'subscription_confirmed',
                    'topics': subscriptions,
                    'timestamp': datetime.now().isoformat()
                }))

            elif message_type == 'ping':
                # Répondre au ping du client
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))

        except json.JSONDecodeError:
            logger.error(f"Erreur de décodage JSON: {text_data}")
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")

    # Méthodes pour différents types de notifications

    async def task_created(self, event):
        """Notifie qu'une nouvelle tâche a été créée"""
        await self.send(text_data=json.dumps({
            'type': 'task_created',
            'task': event['task'],
            'timestamp': datetime.now().isoformat()
        }))

    async def task_updated(self, event):
        """Notifie qu'une tâche a été mise à jour"""
        await self.send(text_data=json.dumps({
            'type': 'task_updated',
            'task': event['task'],
            'changes': event.get('changes', {}),
            'timestamp': datetime.now().isoformat()
        }))

    async def task_deleted(self, event):
        """Notifie qu'une tâche a été supprimée"""
        await self.send(text_data=json.dumps({
            'type': 'task_deleted',
            'task_id': event['task_id'],
            'timestamp': datetime.now().isoformat()
        }))

    async def task_stopped(self, event):
        """Notifie qu'une tâche a été arrêtée"""
        await self.send(text_data=json.dumps({
            'type': 'task_stopped',
            'task_id': event['task_id'],
            'task_name': event.get('task_name'),
            'old_status': event.get('old_status'),
            'new_status': event.get('new_status'),
            'timestamp': datetime.now().isoformat()
        }))

    async def task_resumed(self, event):
        """Notifie qu'une tâche a été reprise"""
        await self.send(text_data=json.dumps({
            'type': 'task_resumed',
            'task_id': event['task_id'],
            'task_name': event.get('task_name'),
            'status': event.get('status'),
            'timestamp': datetime.now().isoformat()
        }))

    async def task_status_changed(self, event):
        """Notifie qu'un statut de tâche a changé"""
        await self.send(text_data=json.dumps({
            'type': 'task_status_changed',
            'task_id': event['task_id'],
            'task_name': event.get('task_name'),
            'old_status': event.get('old_status'),
            'new_status': event.get('new_status'),
            'progress': event.get('progress', 0),
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_created(self, event):
        """Notifie qu'un nouveau workflow a été créé"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_created',
            'workflow': event['workflow'],
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_updated(self, event):
        """Notifie qu'un workflow a été mis à jour"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_updated',
            'workflow': event['workflow'],
            'changes': event.get('changes', {}),
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_deleted(self, event):
        """Notifie qu'un workflow a été supprimé"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_deleted',
            'workflow_id': event['workflow_id'],
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_stopped(self, event):
        """Notifie qu'un workflow a été arrêté"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_stopped',
            'workflow_id': event['workflow_id'],
            'workflow_name': event.get('workflow_name'),
            'old_status': event.get('old_status'),
            'new_status': event.get('new_status'),
            'stopped_tasks': event.get('stopped_tasks', []),
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_resumed(self, event):
        """Notifie qu'un workflow a été repris"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_resumed',
            'workflow_id': event['workflow_id'],
            'workflow_name': event.get('workflow_name'),
            'new_status': event.get('new_status'),
            'resumed_tasks': event.get('resumed_tasks', []),
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_status_changed(self, event):
        """Notifie qu'un statut de workflow a changé"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_status_changed',
            'workflow_id': event['workflow_id'],
            'workflow_name': event.get('workflow_name'),
            'old_status': event.get('old_status'),
            'new_status': event.get('new_status'),
            'timestamp': datetime.now().isoformat()
        }))


class WorkflowUpdatesConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket spécifique aux workflows.
    Les clients se connectent à ws://localhost:8001/ws/workflows/ pour recevoir les updates.
    """

    async def connect(self):
        """Appelé quand un client WebSocket se connecte"""
        self.group_name = 'workflow_updates'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket Workflow connecté: {self.channel_name}")

        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connecté aux mises à jour des workflows',
            'timestamp': datetime.now().isoformat()
        }))

    async def disconnect(self, close_code):
        """Appelé quand un client WebSocket se déconnecte"""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket Workflow déconnecté: {self.channel_name}")

    async def receive(self, text_data):
        """Reçoit un message du client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))

        except json.JSONDecodeError:
            logger.error(f"Erreur de décodage JSON: {text_data}")
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")

    # Méthodes de notification (similaires à TaskUpdatesConsumer)
    async def workflow_created(self, event):
        await self.send(text_data=json.dumps({
            'type': 'workflow_created',
            'workflow': event['workflow'],
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_updated(self, event):
        await self.send(text_data=json.dumps({
            'type': 'workflow_updated',
            'workflow': event['workflow'],
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'workflow_deleted',
            'workflow_id': event['workflow_id'],
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_stopped(self, event):
        await self.send(text_data=json.dumps({
            'type': 'workflow_stopped',
            'workflow_id': event['workflow_id'],
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_resumed(self, event):
        await self.send(text_data=json.dumps({
            'type': 'workflow_resumed',
            'workflow_id': event['workflow_id'],
            'timestamp': datetime.now().isoformat()
        }))
