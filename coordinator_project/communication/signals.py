"""
Signaux Django pour le module de communication.
Gère les événements et notifications dans le système.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


def broadcast_to_websocket(group_name: str, message_type: str, data: dict):
    """
    Envoie un message à un groupe WebSocket.

    Args:
        group_name: Nom du groupe WebSocket
        message_type: Type de message
        data: Données à envoyer
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': message_type,
                    **data
                }
            )
            logger.debug(f"Message WebSocket envoyé au groupe {group_name}: {message_type}")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message WebSocket: {e}")
