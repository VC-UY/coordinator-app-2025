# -*- coding: utf-8 -*-

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime

logger = logging.getLogger(__name__)


class VolunteerUpdatesConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour les mises à jour en temps réel des volontaires.
    Les coordinateurs se connectent à ws://localhost:8000/ws/volunteers/ pour recevoir les updates.
    """

    async def connect(self):
        """Appelé quand un client WebSocket se connecte"""
        # Ajouter ce consumer au groupe "volunteers_updates"
        self.group_name = 'volunteers_updates'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket Volunteer connecté: {self.channel_name}")

        # Envoyer un message de bienvenue
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connecté au système de mise à jour des volontaires',
            'timestamp': datetime.now().isoformat()
        }))

    async def disconnect(self, close_code):
        """Appelé quand un client WebSocket se déconnecte"""
        # Retirer ce consumer du groupe
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket Volunteer déconnecté: {self.channel_name} (code: {close_code})")

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

    async def volunteer_connected(self, event):
        """Notifie qu'un nouveau volontaire s'est connecté"""
        await self.send(text_data=json.dumps({
            'type': 'volunteer_connected',
            'volunteer': event['volunteer'],
            'timestamp': datetime.now().isoformat()
        }))

    async def volunteer_disconnected(self, event):
        """Notifie qu'un volontaire s'est déconnecté"""
        await self.send(text_data=json.dumps({
            'type': 'volunteer_disconnected',
            'volunteer_id': event['volunteer_id'],
            'volunteer_name': event.get('volunteer_name'),
            'timestamp': datetime.now().isoformat()
        }))

    async def volunteer_status_changed(self, event):
        """Notifie qu'un statut de volontaire a changé"""
        await self.send(text_data=json.dumps({
            'type': 'volunteer_status_changed',
            'volunteer_id': event['volunteer_id'],
            'volunteer_name': event.get('volunteer_name'),
            'old_status': event.get('old_status'),
            'new_status': event.get('new_status'),
            'timestamp': datetime.now().isoformat()
        }))

    async def volunteer_updated(self, event):
        """Notifie qu'un volontaire a été mis à jour"""
        await self.send(text_data=json.dumps({
            'type': 'volunteer_updated',
            'volunteer': event['volunteer'],
            'changes': event.get('changes', {}),
            'timestamp': datetime.now().isoformat()
        }))

    async def volunteer_registered(self, event):
        """Notifie qu'un nouveau volontaire s'est enregistré"""
        await self.send(text_data=json.dumps({
            'type': 'volunteer_registered',
            'volunteer': event['volunteer'],
            'timestamp': datetime.now().isoformat()
        }))

    async def volunteer_activated(self, event):
        """Notifie qu'un volontaire a été activé"""
        await self.send(text_data=json.dumps({
            'type': 'volunteer_activated',
            'volunteer_id': event['volunteer_id'],
            'volunteer_name': event.get('volunteer_name'),
            'timestamp': datetime.now().isoformat()
        }))

    async def volunteer_deactivated(self, event):
        """Notifie qu'un volontaire a été désactivé"""
        await self.send(text_data=json.dumps({
            'type': 'volunteer_deactivated',
            'volunteer_id': event['volunteer_id'],
            'volunteer_name': event.get('volunteer_name'),
            'reason': event.get('reason'),
            'timestamp': datetime.now().isoformat()
        }))
