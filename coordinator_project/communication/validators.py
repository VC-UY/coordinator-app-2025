"""
Validateurs pour les données de communication.
Valide les messages, requêtes et réponses dans le système de coordination.
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception levée lors de la validation de données."""
    pass


def validate_volunteer_data(data: Dict[str, Any]) -> bool:
    """
    Valide les données d'un volontaire.

    Args:
        data: Dictionnaire contenant les données du volontaire

    Returns:
        bool: True si valide

    Raises:
        ValidationError: Si les données sont invalides
    """
    required_fields = ['name', 'username', 'ip_address', 'cpu_cores', 'total_ram']

    for field in required_fields:
        if field not in data or not data[field]:
            raise ValidationError(f"Champ requis manquant: {field}")

    # Valider le nom d'utilisateur (alphanumérique et underscore seulement)
    if not re.match(r'^[a-zA-Z0-9_]+$', data['username']):
        raise ValidationError("Le nom d'utilisateur doit contenir uniquement des lettres, chiffres et underscores")

    # Valider l'adresse IP
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(ip_pattern, data['ip_address']):
        raise ValidationError("Adresse IP invalide")

    # Valider les valeurs numériques
    if not isinstance(data['cpu_cores'], int) or data['cpu_cores'] <= 0:
        raise ValidationError("Le nombre de coeurs CPU doit être un entier positif")

    if not isinstance(data['total_ram'], (int, float)) or data['total_ram'] <= 0:
        raise ValidationError("La RAM totale doit être un nombre positif")

    return True


def validate_manager_data(data: Dict[str, Any]) -> bool:
    """
    Valide les données d'un manager.

    Args:
        data: Dictionnaire contenant les données du manager

    Returns:
        bool: True si valide

    Raises:
        ValidationError: Si les données sont invalides
    """
    required_fields = ['username', 'email', 'password']

    for field in required_fields:
        if field not in data or not data[field]:
            raise ValidationError(f"Champ requis manquant: {field}")

    # Valider l'email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, data['email']):
        raise ValidationError("Adresse email invalide")

    # Valider le mot de passe (minimum 6 caractères)
    if len(data['password']) < 6:
        raise ValidationError("Le mot de passe doit contenir au moins 6 caractères")

    return True


def validate_message_data(data: Dict[str, Any]) -> bool:
    """
    Valide les données d'un message.

    Args:
        data: Dictionnaire contenant les données du message

    Returns:
        bool: True si valide

    Raises:
        ValidationError: Si les données sont invalides
    """
    if not isinstance(data, dict):
        raise ValidationError("Les données du message doivent être un dictionnaire")

    # Vérifier la taille des données (max 10MB)
    import sys
    data_size = sys.getsizeof(str(data))
    if data_size > 10 * 1024 * 1024:
        raise ValidationError("Les données du message sont trop volumineuses (max 10MB)")

    return True


def validate_task_data(data: Dict[str, Any]) -> bool:
    """
    Valide les données d'une tâche.

    Args:
        data: Dictionnaire contenant les données de la tâche

    Returns:
        bool: True si valide

    Raises:
        ValidationError: Si les données sont invalides
    """
    required_fields = ['name', 'command']

    for field in required_fields:
        if field not in data or not data[field]:
            raise ValidationError(f"Champ requis manquant: {field}")

    # Valider le nom de la tâche
    if len(data['name']) < 3:
        raise ValidationError("Le nom de la tâche doit contenir au moins 3 caractères")

    # Valider la commande
    if not isinstance(data['command'], str):
        raise ValidationError("La commande doit être une chaîne de caractères")

    return True


def validate_workflow_data(data: Dict[str, Any]) -> bool:
    """
    Valide les données d'un workflow.

    Args:
        data: Dictionnaire contenant les données du workflow

    Returns:
        bool: True si valide

    Raises:
        ValidationError: Si les données sont invalides
    """
    required_fields = ['name', 'tasks']

    for field in required_fields:
        if field not in data or not data[field]:
            raise ValidationError(f"Champ requis manquant: {field}")

    # Valider le nom du workflow
    if len(data['name']) < 3:
        raise ValidationError("Le nom du workflow doit contenir au moins 3 caractères")

    # Valider les tâches
    if not isinstance(data['tasks'], list):
        raise ValidationError("Les tâches doivent être une liste")

    if len(data['tasks']) == 0:
        raise ValidationError("Le workflow doit contenir au moins une tâche")

    # Valider chaque tâche
    for i, task in enumerate(data['tasks']):
        try:
            validate_task_data(task)
        except ValidationError as e:
            raise ValidationError(f"Erreur dans la tâche {i+1}: {str(e)}")

    return True


def sanitize_string(text: str, max_length: int = 1000) -> str:
    """
    Nettoie et limite une chaîne de caractères.

    Args:
        text: Chaîne à nettoyer
        max_length: Longueur maximale

    Returns:
        str: Chaîne nettoyée
    """
    if not isinstance(text, str):
        text = str(text)

    # Supprimer les caractères de contrôle
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')

    # Limiter la longueur
    if len(text) > max_length:
        text = text[:max_length]

    return text.strip()


def validate_channel_name(channel: str) -> bool:
    """
    Valide un nom de canal Redis.

    Args:
        channel: Nom du canal

    Returns:
        bool: True si valide

    Raises:
        ValidationError: Si le canal est invalide
    """
    if not channel or not isinstance(channel, str):
        raise ValidationError("Le nom du canal doit être une chaîne non vide")

    # Format: category/action (ex: auth/login, task/status)
    pattern = r'^[a-z]+/[a-z_]+$'
    if not re.match(pattern, channel):
        raise ValidationError("Format de canal invalide. Format attendu: 'category/action'")

    return True
