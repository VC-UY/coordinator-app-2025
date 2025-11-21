# -*- coding: utf-8 -*-



import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskUpdatesConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour les mises � jour en temps r�el des t�ches et workflows.
    Les clients se connectent � ws://localhost:8001/ws/tasks/ pour recevoir les updates.
    """

    async def connect(self):
        """Appel� quand un client WebSocket se connecte"""
        # Ajouter ce consumer au groupe "tasks_updates"
        self.group_name = 'tasks_updates'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connect�: {self.channel_name}")

        # Envoyer un message de bienvenue
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connect� au syst�me de mises � jour en temps r�el',
            'timestamp': datetime.now().isoformat()
        }))

    async def disconnect(self, close_code):
        """Appel� quand un client WebSocket se d�connecte"""
        # Retirer ce consumer du groupe
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket d�connect�: {self.channel_name} (code: {close_code})")

    async def receive(self, text_data):
        """
        Appel� quand le serveur re�oit un message du client.
        Le client peut s'abonner � des types sp�cifiques d'�v�nements.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'subscribe':
                # Le client s'abonne � des types sp�cifiques
                subscriptions = data.get('topics', [])
                await self.send(text_data=json.dumps({
                    'type': 'subscription_confirmed',
                    'topics': subscriptions,
                    'timestamp': datetime.now().isoformat()
                }))

            elif message_type == 'ping':
                # R�pondre au ping du client
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))

        except json.JSONDecodeError:
            logger.error(f"Erreur de d�codage JSON: {text_data}")
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")

    # M�thodes pour diff�rents types de notifications

    async def task_created(self, event):
        """Notifie qu'une nouvelle t�che a �t� cr��e"""
        await self.send(text_data=json.dumps({
            'type': 'task_created',
            'task': event['task'],
            'timestamp': datetime.now().isoformat()
        }))

    async def task_updated(self, event):
        """Notifie qu'une t�che a �t� mise � jour"""
        await self.send(text_data=json.dumps({
            'type': 'task_updated',
            'task': event['task'],
            'changes': event.get('changes', {}),
            'timestamp': datetime.now().isoformat()
        }))

    async def task_deleted(self, event):
        """Notifie qu'une t�che a �t� supprim�e"""
        await self.send(text_data=json.dumps({
            'type': 'task_deleted',
            'task_id': event['task_id'],
            'timestamp': datetime.now().isoformat()
        }))

    async def task_stopped(self, event):
        """Notifie qu'une t�che a �t� arr�t�e"""
        await self.send(text_data=json.dumps({
            'type': 'task_stopped',
            'task_id': event['task_id'],
            'task_name': event.get('task_name'),
            'old_status': event.get('old_status'),
            'new_status': event.get('new_status'),
            'timestamp': datetime.now().isoformat()
        }))

    async def task_resumed(self, event):
        """Notifie qu'une t�che a �t� reprise"""
        await self.send(text_data=json.dumps({
            'type': 'task_resumed',
            'task_id': event['task_id'],
            'task_name': event.get('task_name'),
            'status': event.get('status'),
            'timestamp': datetime.now().isoformat()
        }))

    async def task_status_changed(self, event):
        """Notifie qu'un statut de t�che a chang�"""
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
        """Notifie qu'un nouveau workflow a �t� cr��"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_created',
            'workflow': event['workflow'],
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_updated(self, event):
        """Notifie qu'un workflow a �t� mis � jour"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_updated',
            'workflow': event['workflow'],
            'changes': event.get('changes', {}),
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_deleted(self, event):
        """Notifie qu'un workflow a �t� supprim�"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_deleted',
            'workflow_id': event['workflow_id'],
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_stopped(self, event):
        """Notifie qu'un workflow a �t� arr�t�"""
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
        """Notifie qu'un workflow a �t� repris"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_resumed',
            'workflow_id': event['workflow_id'],
            'workflow_name': event.get('workflow_name'),
            'new_status': event.get('new_status'),
            'resumed_tasks': event.get('resumed_tasks', []),
            'timestamp': datetime.now().isoformat()
        }))

    async def workflow_status_changed(self, event):
        """Notifie qu'un statut de workflow a chang�"""
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
    Consumer WebSocket sp�cifique aux workflows.
    Les clients se connectent � ws://localhost:8001/ws/workflows/ pour recevoir les updates.
    """

    async def connect(self):
        """Appel� quand un client WebSocket se connecte"""
        self.group_name = 'workflow_updates'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket Workflow connect�: {self.channel_name}")

        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connect� aux mises � jour des workflows',
            'timestamp': datetime.now().isoformat()
        }))

    async def disconnect(self, close_code):
        """Appel� quand un client WebSocket se d�connecte"""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket Workflow d�connect�: {self.channel_name}")

    async def receive(self, text_data):
        """Re�oit un message du client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))

        except json.JSONDecodeError:
            logger.error(f"Erreur de d�codage JSON: {text_data}")
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")

    # M�thodes de notification (similaires � TaskUpdatesConsumer)
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
