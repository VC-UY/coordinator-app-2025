"""
Handler pour l'enregistrement de tous les messages Redis dans la base de données.
"""
import logging
import json
import traceback
from datetime import datetime, timezone
from message_logging.models import MessageLog
from redis_communication.message import Message

logger = logging.getLogger(__name__)

def log_all_messages(channel: str, message: Message):
    """
    Enregistre tous les messages reçus dans la collection MessageLog.
    """
    try:
        # Ignorer les messages de heartbeat pour ne pas polluer les logs
        if 'heartbeat' in channel:
            return

        # Déterminer les types et IDs
        sender_id = 'unknown'
        sender_type = 'unknown'
        
        if message.sender:
            sender_id = message.sender.get('id', 'unknown')
            sender_type = message.sender.get('type', 'unknown')
            
        # Créer le log
        log_entry = MessageLog(
            sender_type=sender_type,
            sender_id=sender_id,
            channel=channel,
            request_id=message.request_id,
            message_type=message.type,
            content=json.dumps(message.data),
            timestamp=datetime.now(timezone.utc),
            is_processed=True 
        )
        log_entry.save()
        
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du message: {e}")
        # Ne pas afficher le traceback complet pour chaque erreur de log pour éviter de spammer
