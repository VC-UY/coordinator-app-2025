"""
Gestionnaires d'événements pour les messages Redis.
Inclut les gestionnaires pour l'authentification des managers et des volontaires.
"""

import logging
import json
import os
import uuid
import time
from typing import Dict, Any, Optional
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings

from manager.models import Manager
from volunteer.models import Volunteer
from .message import Message, MessageType
from .utils import generate_token

logger = logging.getLogger(__name__)


def verify_volunteer_password(plain_password: str, stored_password: str) -> bool:
    """Vérifie un mot de passe volontaire (hash Django ou legacy en clair)."""
    if check_password(plain_password, stored_password):
        return True
    return stored_password == plain_password


def hash_volunteer_password(password: str) -> str:
    """Hash un mot de passe volontaire pour stockage."""
    return make_password(password)


# Répertoire pour stocker les requêtes en attente
PENDING_REQUESTS_DIR = os.path.join(settings.BASE_DIR, 'pending_requests')
os.makedirs(PENDING_REQUESTS_DIR, exist_ok=True)

def save_pending_request(request_id: str, data: Dict[str, Any]):
    """
    Enregistre une requête en attente dans un fichier.
    
    Args:
        request_id: ID de la requête
        data: Données de la requête
    """
    filename = os.path.join(PENDING_REQUESTS_DIR, f"{request_id}.json")
    with open(filename, 'w') as f:
        json.dump({
            'data': data,
            'timestamp': time.time()
        }, f)
    
    logger.debug(f"Requête {request_id} enregistrée dans {filename}")

def get_pending_request(request_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère une requête en attente.
    
    Args:
        request_id: ID de la requête
        
    Returns:
        Dict ou None: Données de la requête si trouvée, None sinon
    """
    filename = os.path.join(PENDING_REQUESTS_DIR, f"{request_id}.json")
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de la requête {request_id}: {e}")
        return None

def delete_pending_request(request_id: str) -> bool:
    """
    Supprime une requête en attente.
    
    Args:
        request_id: ID de la requête
        
    Returns:
        bool: True si supprimée, False sinon
    """
    filename = os.path.join(PENDING_REQUESTS_DIR, f"{request_id}.json")
    if not os.path.exists(filename):
        return False
    
    try:
        os.remove(filename)
        logger.debug(f"Requête {request_id} supprimée")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la requête {request_id}: {e}")
        return False


def is_machine_already_registered(machine_info: Dict[str, Any]) -> Optional[Volunteer]:
    """
    Vérifie si une machine est déjà enregistrée en se basant sur ses caractéristiques matérielles.
    
    Args:
        machine_info: Informations détaillées de la machine
        
    Returns:
        Optional[Volunteer]: Le volontaire existant si trouvé, None sinon
    """
    if not machine_info:
        return None
    
    # Approche 0: Recherche par adresse MAC (identifiant unique et stable)
    if 'adresse_mac' in machine_info and machine_info['adresse_mac']:
        mac_address = machine_info['adresse_mac']
        logger.debug(f"Recherche de machine par adresse MAC: {mac_address}")
        volunteer = Volunteer.objects(machine_info__adresse_mac=mac_address).first()
        if volunteer:
            logger.info(f"Machine identifiée par adresse MAC: {volunteer.name} (ID: {volunteer.id})")
            return volunteer
        else:
            logger.debug(f"Aucune machine trouvée avec l'adresse MAC: {mac_address}")
    
    # Approche 1: Recherche par caractéristiques matérielles spécifiques
    # Critères d'identification de la machine
    primary_criteria = {}
    secondary_criteria = {}
    
    # Caractéristiques primaires (très stables)
    criteria_count = 0
    
    # CPU - Type et nombre de coeurs (très stable)
    if 'cpu' in machine_info:
        cpu_info = machine_info['cpu']
        if 'modele' in cpu_info and cpu_info['modele']:
            primary_criteria['machine_info__cpu__modele'] = cpu_info['modele']
            criteria_count += 1
        if 'coeurs_physiques' in cpu_info:
            primary_criteria['machine_info__cpu__coeurs_physiques'] = cpu_info['coeurs_physiques']
            criteria_count += 1
        if 'coeurs_logiques' in cpu_info:
            primary_criteria['machine_info__cpu__coeurs_logiques'] = cpu_info['coeurs_logiques']
            criteria_count += 1
        if 'frequence' in cpu_info and 'min' in cpu_info['frequence']:
            primary_criteria['machine_info__cpu__frequence__min'] = cpu_info['frequence']['min']
            criteria_count += 1
        if 'frequence' in cpu_info and 'max' in cpu_info['frequence']:
            primary_criteria['machine_info__cpu__frequence__max'] = cpu_info['frequence']['max']
            criteria_count += 1
    
    # Architecture du système (très stable)
    if 'os' in machine_info and 'architecture' in machine_info['os']:
        arch = machine_info['os']['architecture']
        if arch:
            primary_criteria['machine_info__os__architecture'] = arch
            criteria_count += 1
        if 'nom' in machine_info['os']:
            primary_criteria['machine_info__os__nom'] = machine_info['os']['nom']
            criteria_count += 1
    
    # RAM totale (très stable)
    if 'memoire' in machine_info and 'ram' in machine_info['memoire']:
        ram_info = machine_info['memoire']['ram']
        if 'total' in ram_info:
            primary_criteria['machine_info__memoire__ram__total'] = ram_info['total']
            criteria_count += 1
        
        ram_info = machine_info['memoire']['cache']
        if 'total' in ram_info:
            primary_criteria['machine_info__memoire__cache__total'] = ram_info['total']
            criteria_count += 1
        
        ram_info = machine_info['memoire']['swap']
        if 'total' in ram_info:
            primary_criteria['machine_info__memoire__swap__total'] = ram_info['total']
            criteria_count += 1
    
    # Disque total (très stable)
    if 'disque' in machine_info and 'total' in machine_info['disque']:
        disk_total = machine_info['disque']['total']
        primary_criteria['machine_info__disque__total'] = disk_total
        criteria_count += 1
    
    # Caractéristiques secondaires (peuvent changer, mais rarement)
    # Nom d'hôte
    if 'os' in machine_info and 'hostname' in machine_info['os']:
        hostname = machine_info['os']['hostname']
        if hostname:
            secondary_criteria['name__contains'] = hostname
    
    # Carte mère et BIOS
    if 'bios_carte_mere' in machine_info and 'BIOS' in machine_info['bios_carte_mere'] and 'Fabricant' in  machine_info['bios_carte_mere']['BIOS']:
        primary_criteria['machine_info__bios_carte_mere__BIOS__Fabricant'] = machine_info['bios_carte_mere']['BIOS']['Fabricant']
        criteria_count += 1
    
    if 'bios_carte_mere' in machine_info and 'mother_board' in machine_info['bios_carte_mere'] and 'Fabricant' in  machine_info['bios_carte_mere']['mother_board']:
        primary_criteria['machine_info__bios_carte_mere__mother_board__Fabricant'] = machine_info['bios_carte_mere']['mother_board']['Modele']
        criteria_count += 1
    
    
    # Recherche avec les critères primaires (très stables)
    if criteria_count >= 10:
        logger.debug(f"Recherche de machine avec critères primaires: {primary_criteria}")
        volunteer = Volunteer.objects(**primary_criteria).first()
        if volunteer:
            logger.info(f"Machine identifiée par caractéristiques matérielles primaires: {volunteer.name} (ID: {volunteer.id})")
            return volunteer
        else: 
            logger.debug(f"Aucune machine trouvée avec {criteria_count} critères primaires seuls")
            logger.debug("Essai 1 critère primaire ")
            v = Volunteer.objects(**{'machine_info__cpu__coeurs_physiques': 2})
            logger.debug(f"Resultats: {[vv.to_mongo().to_dict() for vv in v]}")
    
    # Si aucune correspondance avec les critères primaires, essayer avec une combinaison de primaires et secondaires
    if criteria_count >= 8 and secondary_criteria:
        combined_criteria = {**primary_criteria, **secondary_criteria}
        logger.debug(f"Recherche de machine avec critères combinés: {combined_criteria}")
        volunteer = Volunteer.objects(**combined_criteria).first()
        if volunteer:
            logger.info(f"Machine identifiée par combinaison de caractéristiques: {volunteer.name} (ID: {volunteer.id})")
            return volunteer
    
    # Approche 2: Recherche par similarité globale
    # Si aucune correspondance exacte n'est trouvée, on peut rechercher les machines les plus similaires
    # et vérifier si la similarité est suffisante pour considérer que c'est la même machine
    
    # Cette partie pourrait être implémentée dans une version future
    
    return None

# Gestionnaires génériques

def log_message_handler(channel: str, message: Message):
    """
    Gestionnaire simple qui journalise les messages reçus.
    
    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
    """
    logger.info(f"Message reçu sur {channel}: {message.request_id} de {message.sender}")
    logger.debug(f"Contenu: {message.data}")

def heartbeat_handler(channel: str, message: Message):
    """
    Gestionnaire pour les messages de heartbeat.
    
    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
    """
    sender = message.sender if isinstance(message.sender, dict) else {}
    sender_type = sender.get('type', 'unknown')
    sender_id = sender.get('id', 'unknown')
    data = message.data or {}
    volunteer_id = data.get('volunteer_id') or (sender_id if sender_type == 'volunteer' else None)
    if volunteer_id:
        try:
            from volunteer.presence import mark_offline, mark_online

            status = data.get("status") or "available"
            preferences = data.get("preferences")
            resources = data.get("resources")

            if status == "offline":
                mark_offline(volunteer_id, reason="schedule")
            else:
                from volunteer.models import Volunteer
                from volunteer.presence import is_online
                volunteer = Volunteer.objects(id=volunteer_id).first()
                was_offline = volunteer and not is_online(volunteer)
                mark_online(
                    volunteer_id,
                    status=status,
                    preferences=preferences,
                    resources=resources,
                )
                from redis_communication.task_status_handlers import (
                    _trigger_coordinator_assignment,
                )
                _trigger_coordinator_assignment()
                if was_offline:
                    logger.info(
                        "Volontaire %s de retour en ligne (%s) — republication des tâches",
                        volunteer_id, status,
                    )
        except Exception as exc:
            logger.warning("Heartbeat volontaire ignore: %s", exc)
    logger.debug(f"Heartbeat reçu de {sender_type}:{sender_id}")


def volunteer_heartbeat_handler(channel: str, message: Message):
    heartbeat_handler(channel, message)


def volunteer_disconnect_handler(channel: str, message: Message):
    data = message.data or {}
    sender = message.sender if isinstance(message.sender, dict) else {}
    volunteer_id = data.get('volunteer_id') or sender.get('id')
    if volunteer_id:
        try:
            from volunteer.presence import mark_offline
            mark_offline(volunteer_id, reason='disconnect')
        except Exception as exc:
            logger.warning("Disconnect volontaire ignore: %s", exc)

def error_handler(channel: str, message: Message):
    """
    Gestionnaire pour les messages d'erreur.
    
    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
    """
    error_data = message.data
    error_msg = error_data.get('message', 'Erreur inconnue')
    error_code = error_data.get('code', 0)
    
    logger.error(f"Erreur sur {channel}: [{error_code}] {error_msg}")
    logger.error(f"Détails: {error_data}")

# Gestionnaires pour l'authentification des managers

def manager_registration_handler(channel: str, message: Message):
    """
    Gestionnaire pour l'enregistrement des managers.
    
    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
    """
    from .client import RedisClient
    logger.setLevel(logging.INFO)
    logger.warning(f"Demande d'enregistrement de manager reçue: {message.data}")
    
    # Récupérer les données du message
    data = message.data
    request_id = message.request_id

    
    # Vérifier si data est un dictionnaire vide ou None
    if not data or not isinstance(data, dict):
        logger.error(f"Données invalides reçues: {data}")
        
        # Envoyer une réponse d'erreur
        client = RedisClient.get_instance()
        client.publish('auth/register_response', {
            'status': 'error',
            'message': "Format de données invalide"
        }, request_id=request_id)
        return
        
    # Compatibilité avec le format de données du manager
    # Si les données sont dans un format différent, essayer de les extraire
    if 'username' not in data and 'email' not in data and 'password' not in data:
        # Essayer de récupérer les données depuis le message original
        original_dict = message.to_dict()
        logger.info(f"Tentative d'extraction des données depuis le message original: {original_dict}")
        
        # Vérifier si les données sont directement dans le message
        if isinstance(original_dict.get('data'), dict):
            data = original_dict.get('data')
            logger.info(f"Données extraites du message original: {data}")
    
    # Vérifier que les données sont complètes
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data:
            logger.error(f"Champ requis manquant: {field}")
            
            # Envoyer une réponse d'erreur
            client = RedisClient.get_instance()
            client.publish('auth/register_response', {
                'status': 'error',
                'message': f"Champ requis manquant: {field}"
            }, request_id=request_id, message_type='response')
            return
    
    # Enregistrer la requête en attente
    save_pending_request(request_id, data)
    
    # Récupérer les données
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    
    try:
        # Vérifier si MongoDB est disponible
        try:
            # Vérifier si le manager existe déjà            
            existing_email = Manager.objects(email=email).first()
            if existing_email:
                logger.warning(f"L'email {email} est déjà utilisé, envoie du message d'erreur")
                
                # Envoyer une réponse d'erreur
                client = RedisClient.get_instance()
                client.publish('auth/register_response', {
                    'status': 'error',
                    'message': "Cet email est déjà utilisé"
                }, request_id=request_id, message_type="response")
                logger.warning(f"Message publié sur 'auth/register_response' avec le request_id: {request_id}")
                
                # Supprimer la requête en attente
                delete_pending_request(request_id)
                return
        except Exception as mongo_error:
            # Si MongoDB n'est pas disponible, on enregistre l'erreur mais on continue
            logger.error(f"Erreur de connexion à MongoDB: {mongo_error}")
            logger.info("Poursuite de l'enregistrement sans vérification de duplicata (MongoDB indisponible)")
        
        # Créer le manager
        hashed_password = make_password(password)
        try:                
            # Créer le nouveau manager
            manager = Manager(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=hashed_password,
                status='active'  
            )
            manager.save()
            logger.warning(f"NOUVEAU MANAGER: {username} créé avec succès (ID: {manager.id})")
        except Exception as mongo_save_error:
            logger.error(f"Impossible de sauvegarder le manager dans MongoDB: {mongo_save_error}")
            # On simule un succès même si MongoDB n'est pas disponible
            # Cela permet au manager de continuer à fonctionner même sans MongoDB
            logger.warning("Simulation de succès d'enregistrement (MongoDB indisponible)")
        
        logger.warning(f"Manager {username} enregistré avec succès (ID: {manager.id})")
        
        # Envoyer une réponse de succès
        client = RedisClient.get_instance()
        client.publish('auth/register_response', {
            'status': 'success',
            'message': 'Enregistrement réussi',
            'manager_id': str(manager.id),
            'username': manager.username,
            'first_name': manager.first_name,
            'last_name': manager.last_name,
            'email': manager.email
        }, request_id=request_id, message_type="response")
        
        # Log pour vérifier que le message a bien été publié
        logger.warning(f"Réponse publiée sur auth/register_response avec request_id: {request_id}")
        
        # Supprimer la requête en attente
        delete_pending_request(request_id)
        
    except Exception as e:
        import traceback
        logger.error(f"Erreur lors de l'enregistrement du manager: {e}")
        logger.error(traceback.format_exc())
        
        # Envoyer une réponse d'erreur
        client = RedisClient.get_instance()
        client.publish('auth/register_response', {
            'status': 'error',
            'message': str(e)
        }, request_id=request_id, message_type="response")
        
        # Supprimer la requête en attente
        delete_pending_request(request_id)

def manager_login_handler(channel: str, message: Message):
    """
    Gestionnaire pour l'authentification des managers.
    
    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
    """
    from .client import RedisClient
    
    logger.info(f"Demande d'authentification de manager reçue: {message.request_id}")
    
    # Récupérer les données du message
    data = message.data
    request_id = message.request_id
    
    # Vérifier que les données sont complètes
    required_fields = ['username', 'password']
    for field in required_fields:
        if field not in data:
            logger.error(f"Champ requis manquant: {field}")
            
            # Envoyer une réponse d'erreur
            client = RedisClient.get_instance()
            client.publish('auth/login_response', {
                'status': 'error',
                'message': f"Champ requis manquant: {field}"
            }, request_id=request_id, message_type="response")
            return
    
    # Enregistrer la requête en attente
    save_pending_request(request_id, data)
    
    # Récupérer les données
    username = data.get('username')
    password = data.get('password')
    
    try:
        # Rechercher le manager
        try:
            manager = Manager.objects(username=username).first()
            if not manager:
                logger.warning(f"Manager {username} introuvable")
                
                # Envoyer une réponse d'erreur
                response = Message.create_response(message, {
                    'status': 'error',
                    'message': 'Identifiants invalides'
                })
                client = RedisClient.get_instance()
                client.publish('auth/login_response', response.to_dict(), request_id=request_id)
                
                # Supprimer la requête en attente
                delete_pending_request(request_id)
                return
        except Exception as mongo_error:
            logger.error(f"Erreur de connexion à MongoDB: {mongo_error}")
            
            # Envoyer une réponse d'erreur
            response = Message.create_response(message, {
                'status': 'error',
                'message': 'Identifiants invalides'
            })
            client = RedisClient.get_instance()
            client.publish('auth/login_response', response.to_dict(), request_id=request_id)
            
            # Supprimer la requête en attente
            delete_pending_request(request_id)
            return
        
        # Vérifier le mot de passe
        try:
            if not check_password(password, manager.password):
                logger.warning(f"Mot de passe incorrect pour {username}")
                
                # Envoyer une réponse d'erreur
                response = Message.create_response(message, {
                    'status': 'error',
                    'message': 'Identifiants invalides'
                })
                client = RedisClient.get_instance()
                client.publish('auth/login_response', response.to_dict(), request_id=request_id)
                
                # Supprimer la requête en attente
                delete_pending_request(request_id)
                return
        except Exception as pwd_error:
            logger.error(f"Erreur lors de la vérification du mot de passe: {pwd_error}")
            
            # Envoyer une réponse d'erreur
            response = Message.create_response(message, {
                'status': 'error',
                'message': 'Identifiants invalides'
            })
            client = RedisClient.get_instance()
            client.publish('auth/login_response', response.to_dict(), request_id=request_id)
            
            # Supprimer la requête en attente
            delete_pending_request(request_id)
            return
        
        # Vérifier que le compte est actif
        if manager.status != 'active':
            logger.warning(f"Le compte {username} n'est pas actif")
            
            # Envoyer une réponse d'erreur
            client = RedisClient.get_instance()
            client.publish('auth/login_response', {
                'status': 'error',
                'message': "Ce compte n'est pas actif"
            }, request_id=request_id, message_type="response")
            
            # Supprimer la requête en attente
            delete_pending_request(request_id)
            return
        
        # Générer un token JWT et un refresh token
        token = generate_token(str(manager.id), 'manager', 24)  # 24 heures
        refresh_token = generate_token(str(manager.id), 'manager', 168)  # 7 jours
        
        # Mettre à jour la date de dernière connexion
        try:
            manager.last_login = datetime.utcnow()
            manager.save()
        except Exception as save_error:
            logger.error(f"Impossible de mettre à jour la date de dernière connexion: {save_error}")
            # On continue sans mettre à jour la date de dernière connexion
        
        logger.info(f"Manager {username} authentifié avec succès")
        
        # Envoyer une réponse de succès
        client = RedisClient.get_instance()
        client.publish('auth/login_response', {
            'status': 'success',
            'message': 'Authentification réussie',
            'token': token,
            'refresh_token': refresh_token,
            'manager_id': str(manager.id),
            'username': manager.username,
            'first_name': manager.first_name,
            'last_name': manager.last_name,
            'email': manager.email
        }, request_id=request_id, message_type="response")
        
        # Supprimer la requête en attente
        delete_pending_request(request_id)
        
    except Exception as e:
        import traceback
        logger.error(f"Erreur lors de l'authentification du manager: {e}")
        logger.error(traceback.format_exc())
        
        # Envoyer une réponse d'erreur
        client = RedisClient.get_instance()
        client.publish('auth/login_response', {
            'status': 'error',
            'message': str(e)
        }, request_id=request_id, message_type="response")
        
        # Supprimer la requête en attente
        delete_pending_request(request_id)

# Gestionnaires pour l'authentification des volontaires

def volunteer_registration_handler(channel: str, message: Message):
    """
    Gestionnaire pour l'enregistrement des volontaires.
    
    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
    """
    from .client import RedisClient
    
    logger.info(f"Demande d'enregistrement de volontaire reçue: {message.request_id}")
    
    # Récupérer les données du message
    data = message.data
    request_id = message.request_id
    
    # Vérifier que les données sont complètes
    required_fields = ['name', 'cpu_cores', 'ram_mb', 'disk_gb', 'username', 'password']
    for field in required_fields:
        if field not in data:
            logger.error(f"Champ requis manquant: {field}")
            
            # Envoyer une réponse d'erreur
            client = RedisClient.get_instance()
            client.publish('auth/volunteer_register_response', {
                'status': 'error',
                'message': f"Champ requis manquant: {field}"
            }, request_id=request_id)
            return
    
    # Enregistrer la requête en attente
    save_pending_request(request_id, data)
    
    # Extraire les informations de la machine avant d'y accéder
    machine_info = data.get('machine_info', {}) or {}

    # Récupérer les informations de base
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    ip_address = data.get('ip_address') or '0.0.0.0'  # interne uniquement, non exposé
    mac_address = data.get('mac_address') or machine_info.get('adresse_mac', '')
    cpu_cores = data.get('cpu_cores')
    ram_mb = data.get('ram_mb')
    disk_gb = data.get('disk_gb')
    
    # Déterminer le système d'exploitation
    os_info = "Unknown"
    if machine_info and 'os' in machine_info:
        os_info = f"{machine_info['os'].get('nom', 'Unknown')} {machine_info['os'].get('version', '')}"
    
    # Déterminer le modèle CPU
    cpu_model = "Unknown"
    if machine_info and 'cpu' in machine_info:
        cpu_model = machine_info['cpu'].get('type', 'Unknown')
    
    # Déterminer les informations GPU
    gpu_available = False
    gpu_model = None
    gpu_memory = None
    if machine_info and 'gpu' in machine_info:
        gpu_available = machine_info['gpu'].get('Disponible', False)
        if gpu_available:
            gpu_model = machine_info['gpu'].get('model', 'Unknown')
            gpu_memory = machine_info['gpu'].get('memory', 0)
    
    try:
        # Vérifier d'abord si la machine est déjà enregistrée en se basant sur ses caractéristiques matérielles
        existing_machine = is_machine_already_registered(machine_info)
        if existing_machine:
            logger.warning(f"La machine avec les caractéristiques fournies est déjà enregistrée sous le nom {existing_machine.name} (ID: {existing_machine.id})")
            
            # Mettre à jour les informations du volontaire existant si nécessaire
            existing_machine.username = username
            existing_machine.password = hash_volunteer_password(password)
            existing_machine.name = name
            existing_machine.current_status = 'available'
            existing_machine.last_activity = datetime.utcnow()
            if mac_address and machine_info:
                machine_info = dict(machine_info)
                machine_info['adresse_mac'] = mac_address
            
            # Mettre à jour les informations détaillées de la machine
            if machine_info:
                # Supprimer les informations trop détaillées qui pourraient causer des problèmes
                if 'partitions_disque' in machine_info:
                    del machine_info['partitions_disque']
                existing_machine.machine_info = machine_info
            
            existing_machine.save()

            logger.info(f"Informations du volontaire {name} (ID: {existing_machine.id}) mises à jour")

            # Envoyer une notification WebSocket aux coordinateurs
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync

                channel_layer = get_channel_layer()
                if channel_layer:
                    volunteer_data = {
                        'id': str(existing_machine.id),
                        'name': existing_machine.name,
                        'username': existing_machine.username,
                        'status': existing_machine.current_status,
                        'cpu_model': existing_machine.cpu_model,
                        'cpu_cores': existing_machine.cpu_cores,
                        'total_ram': existing_machine.total_ram,
                        'operating_system': existing_machine.operating_system,
                        'ip_address': existing_machine.ip_address
                    }

                    async_to_sync(channel_layer.group_send)(
                        'volunteers_updates',
                        {
                            'type': 'volunteer_connected',
                            'volunteer': volunteer_data
                        }
                    )
                    logger.info(f"Notification WebSocket envoyée pour la reconnexion du volontaire {name}")
            except Exception as ws_error:
                logger.error(f"Erreur lors de l'envoi de la notification WebSocket: {ws_error}")

            # Générer un nouveau token
            token = generate_token(str(existing_machine.id), 'volunteer', 24)  # 24 heures

            # Envoyer une réponse de succès avec les informations mises à jour
            client = RedisClient.get_instance()
            client.publish('auth/volunteer_register_response', {
                'status': 'success',
                'message': 'Machine déjà enregistrée, informations mises à jour',
                'volunteer_id': str(existing_machine.id),
                'username': username,
                'token': token,
                'is_update': True
            }, request_id=request_id)

            # Supprimer la requête en attente
            delete_pending_request(request_id)
            return
        
        # Si la machine n'est pas déjà enregistrée, vérifier si le nom d'utilisateur est déjà utilisé
        existing_volunteer = Volunteer.objects(username=username).first()
        if existing_volunteer:
            logger.warning(f"Le volontaire avec username {username} existe déjà")
            
            # Envoyer une réponse d'erreur
            client = RedisClient.get_instance()
            client.publish('auth/volunteer_register_response', {
                'status': 'error',
                'message': "Ce nom d'utilisateur est déjà utilisé"
            }, request_id=request_id)
            
            # Supprimer la requête en attente
            delete_pending_request(request_id)
            return
        
        # Créer le volontaire avec les nouvelles informations
        volunteer = Volunteer(
            name=name,
            username=username,
            password=hash_volunteer_password(password),
            cpu_model=cpu_model,
            cpu_cores=cpu_cores,
            total_ram=ram_mb,
            available_storage=disk_gb,
            operating_system=os_info,
            gpu_available=gpu_available,
            gpu_model=gpu_model,
            gpu_memory=gpu_memory,
            ip_address='0.0.0.0',
            communication_port=int(os.environ.get('VOLUNTEER_API_PORT', 8003)),
            current_status='available',
            performance={
                'tasks_total': 0,
                'tasks_completed': 0,
                'tasks_failed': 0,
                'trust_score': 50.0,  # Score initial de confiance à 50%
                'avg_completion_time': 0,
                'total_completion_time': 0,
                'successful_assignments': 0,
                'failed_assignments': 0
            }
        )
        
        # Stocker les informations détaillées de la machine
        # Limiter la taille des informations pour éviter les problèmes de sérialisation
        if machine_info:
            if 'partitions_disque' in machine_info:
                del machine_info['partitions_disque']
            if mac_address:
                machine_info = dict(machine_info)
                machine_info['adresse_mac'] = mac_address
            volunteer.machine_info = machine_info
        
        volunteer.ip_address = '0.0.0.0'
        volunteer.save()

        logger.info(f"Volontaire {name} ({username}) enregistré avec succès (ID: {volunteer.id})")

        # Envoyer une notification WebSocket aux coordinateurs
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                volunteer_data = {
                    'id': str(volunteer.id),
                    'name': volunteer.name,
                    'username': volunteer.username,
                    'status': volunteer.current_status,
                    'cpu_model': volunteer.cpu_model,
                    'cpu_cores': volunteer.cpu_cores,
                    'total_ram': volunteer.total_ram,
                    'operating_system': volunteer.operating_system,
                    'ip_address': volunteer.ip_address
                }

                async_to_sync(channel_layer.group_send)(
                    'volunteers_updates',
                    {
                        'type': 'volunteer_registered',
                        'volunteer': volunteer_data
                    }
                )
                logger.info(f"Notification WebSocket envoyée pour le nouveau volontaire {name}")
        except Exception as ws_error:
            logger.error(f"Erreur lors de l'envoi de la notification WebSocket: {ws_error}")

        # Envoyer une réponse de succès
        client = RedisClient.get_instance()
        client.publish('auth/volunteer_register_response', {
            'status': 'success',
            'message': 'Volontaire enregistré avec succès',
            'volunteer_id': str(volunteer.id),
            'username': username,
            'token': str(uuid.uuid4())  # Générer un token d'authentification
        }, request_id=request_id)

        # Supprimer la requête en attente
        delete_pending_request(request_id)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du volontaire: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Envoyer une réponse d'erreur
        client = RedisClient.get_instance()
        client.publish('auth/volunteer_register_response', {
            'status': 'error',
            'message': str(e)
        }, request_id=request_id)
        
        # Supprimer la requête en attente
        delete_pending_request(request_id)

def volunteer_login_handler(channel: str, message: Message):
    """
    Gestionnaire pour l'authentification des volontaires.
    
    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
    """
    from .client import RedisClient
    
    logger.info(f"Demande d'authentification de volontaire reçue: {message.request_id}")
    
    # Récupérer les données du message
    data = message.data
    request_id = message.request_id
    
    # Vérifier que les données sont complètes
    required_fields = ['username', 'password']
    for field in required_fields:
        if field not in data:
            logger.error(f"Champ requis manquant: {field}")
            
            # Envoyer une réponse d'erreur
            client = RedisClient.get_instance()
            client.publish('auth/volunteer_login_response', {
                'status': 'error',
                'message': f"Champ requis manquant: {field}"
            }, request_id=request_id)
            return
    
    # Enregistrer la requête en attente
    save_pending_request(request_id, data)
    
    # Récupérer les données
    username = data.get('username')
    password = data.get('password')
    
    try:
        # Rechercher le volontaire par username
        volunteer = Volunteer.objects(username=username).first()
        if not volunteer:
            logger.warning(f"Volontaire avec username {username} introuvable")
            
            # Envoyer une réponse d'erreur
            client = RedisClient.get_instance()
            client.publish('auth/volunteer_login_response', {
                'status': 'error',
                'message': 'Identifiants invalides'
            }, request_id=request_id)
            
            # Supprimer la requête en attente
            delete_pending_request(request_id)
            return
        
        # Vérifier le mot de passe (hash ou legacy en clair)
        if not verify_volunteer_password(password, volunteer.password):
            logger.warning(f"Mot de passe incorrect pour le volontaire {username}")
            
            # Envoyer une réponse d'erreur
            client = RedisClient.get_instance()
            client.publish('auth/volunteer_login_response', {
                'status': 'error',
                'message': 'Identifiants invalides'
            }, request_id=request_id)
            
            # Supprimer la requête en attente
            delete_pending_request(request_id)
            return
        
        # Générer un token JWT et un refresh token
        token = generate_token(str(volunteer.id), 'volunteer', 24)  # 24 heures
        refresh_token = generate_token(str(volunteer.id), 'volunteer', 168)  # 7 jours
        
        # Mettre à jour la date de dernière activité
        volunteer.last_activity = datetime.utcnow()
        volunteer.current_status = 'available'
        volunteer.save()

        logger.info(f"Volontaire {username} authentifié avec succès")

        # Mettre à jour les informations machine si fournies
        machine_info = data.get('machine_info')
        if machine_info:
            # Limiter la taille des informations pour éviter les problèmes de sérialisation
            if 'partitions_disque' in machine_info:
                del machine_info['partitions_disque']
            volunteer.machine_info = machine_info
            volunteer.save()

        # Envoyer une notification WebSocket aux coordinateurs
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                volunteer_data = {
                    'id': str(volunteer.id),
                    'name': volunteer.name,
                    'username': volunteer.username,
                    'status': volunteer.current_status,
                    'cpu_model': volunteer.cpu_model,
                    'cpu_cores': volunteer.cpu_cores,
                    'total_ram': volunteer.total_ram,
                    'operating_system': volunteer.operating_system,
                    'ip_address': volunteer.ip_address
                }

                async_to_sync(channel_layer.group_send)(
                    'volunteers_updates',
                    {
                        'type': 'volunteer_connected',
                        'volunteer': volunteer_data
                    }
                )
                logger.info(f"Notification WebSocket envoyée pour la connexion du volontaire {username}")
        except Exception as ws_error:
            logger.error(f"Erreur lors de l'envoi de la notification WebSocket: {ws_error}")

        # Envoyer une réponse de succès
        client = RedisClient.get_instance()
        client.publish('auth/volunteer_login_response', {
            'status': 'success',
            'message': 'Authentification réussie',
            'token': token,
            'refresh_token': refresh_token,
            'volunteer_id': str(volunteer.id),
            'username': volunteer.username,
            'name': volunteer.name
        }, request_id=request_id)
        
        # Supprimer la requête en attente
        delete_pending_request(request_id)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'authentification du volontaire: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Envoyer une réponse d'erreur
        client = RedisClient.get_instance()
        client.publish('auth/volunteer_login_response', {
            'status': 'error',
            'message': str(e)
        }, request_id=request_id)
        
        # Supprimer la requête en attente
        delete_pending_request(request_id)

# Dictionnaire des gestionnaires par défaut
DEFAULT_HANDLERS = {
    # Canaux génériques
    "coord/heartbeat": heartbeat_handler,
    "volunteer/heartbeat": volunteer_heartbeat_handler,
    "volunteer/disconnect": volunteer_disconnect_handler,
    "coord/emergency": error_handler,
    "system/error": error_handler,
    
    # Canaux d'authentification des managers
    "auth/register": manager_registration_handler,
    "auth/login": manager_login_handler,
    
    # Canaux d'authentification des volontaires
    "auth/volunteer_register": volunteer_registration_handler,
    "auth/volunteer_login": volunteer_login_handler
}
