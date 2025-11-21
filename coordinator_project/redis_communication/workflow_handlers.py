"""
Gestionnaires pour les workflows dans le système de communication Redis.
Gère les opérations : submission, update, delete, stop, resume des workflows.
"""

import json
import logging
import uuid
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone

from redis_communication.client import RedisClient
from redis_communication.message import Message
from redis_communication.utils import verify_token
from redis_communication.handlers import save_pending_request, delete_pending_request

logger = logging.getLogger(__name__)

def workflow_submission_handler(channel: str, message: Message):
    """
    Gestionnaire pour les soumissions de workflows.
    
    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
    """
    try:
        logger.info(f"Demande de soumission de workflow reçue: {message.to_dict()}")
        
        # Extraire les données du message
        data = message.data
        request_id = message.request_id
        
        
        
        # Enregistrer la requête en attente
        save_pending_request(request_id, data)
        
        # Extraire les informations du workflow
        workflow_id = data.get('workflow_id')
        workflow_name = data.get('workflow_name')
        workflow_type = data.get('workflow_type')
        owner = data.get('owner', '')
        estimated_resources = data.get('estimated_resources', {})
        
        logger.info(f"Workflow {workflow_name} ({workflow_id}) soumis par {owner}")
        
        # Vérifier les ressources estimées
        if not estimated_resources:
            logger.warning(f"Aucune ressource estimée fournie pour le workflow {workflow_id}")
            estimated_resources = {
                "estimated_cpu_cores": 2,
                "estimated_memory_mb": 1024,
                "estimated_disk_space_mb": 500,
                "gpu_required": False
            }


        # Enregistrer le workflow dans la base de données
        from manager.models import Workflow, Manager
        manager = Manager.objects.get(id=owner)
        workflow = Workflow(
            id=workflow_id,
            name=workflow_name,
            description=data.get('description', ''),
            workflow_type=workflow_type,
            owner=manager,
            estimated_resources=estimated_resources,
            priority=data.get('priority', 1),
            attempts=data.get('attempts', 3),  # Nombre de tentatives en cas d'échec
            max_execution_time=data.get('max_execution_time', 3600),  # Temps maximum d'exécution en secondes
            input_data_size=data.get('input_data_size', 0),
        )
        workflow.save()        


        
        # TODO: Rechercher des volontaires disponibles avec les ressources nécessaires
        # Pour l'instant, simuler une réponse positive
        
        # Générer un ID de workflow pour le coordinateur

        # Récupérer la liste des volontaires disponibles depuis la base de données
        from .utils import get_available_volunteers
        assigned_volunteers = get_available_volunteers()
        
        # Si aucun volontaire n'est disponible, utiliser des données de test
        if not assigned_volunteers:
            logger.warning("Aucun volontaire disponible dans la base de données, utilisation de données de test")
            assigned_volunteers = [
                {
                    "volunteer_id": str(uuid.uuid4()),
                    "username": "volunteer1_test",
                    "resources": {
                        "cpu_cores": 1,
                        "memory_mb": 1024,
                        "disk_space_mb": 1024,
                        "gpu": False
                    }
                },
                {
                    "volunteer_id": str(uuid.uuid4()),
                    "username": "volunteer2_test",
                    "resources": {
                        "cpu_cores": 2,
                        "memory_mb": 2048,
                        "disk_space_mb": 2000,
                        "gpu": False
                    }
                }
            ] 
        else:
            logger.error(f"Utilisation de {assigned_volunteers} volontaires réels pour le workflow")
        
        # Envoyer une réponse de succès
        client = RedisClient.get_instance()
        from .utils import get_coordinator_token
        token = get_coordinator_token()
        client.publish('workflow/submit_response', {
            'status': 'success',
            'message': 'Workflow accepté',
            'workflow_id': str(workflow.id),
            'volunteers': assigned_volunteers
        }, request_id=request_id, token=token, message_type="response")
        
        logger.info(f"Workflow {workflow.id} accepté")
        
        # Supprimer la requête en attente
        delete_pending_request(request_id)
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la soumission du workflow: {e}")
        logger.error(traceback.format_exc())
        
        try:
            # Récupérer l'ID du workflow s'il existe
            workflow_id = message.data.get('workflow_id', 'inconnu')
            
            # Envoyer une réponse d'erreur
            client = RedisClient.get_instance()
            from .utils import get_coordinator_token
            token = get_coordinator_token()
            client.publish('workflow/submit_response', {
                'status': 'error',
                'message': f"Erreur lors du traitement: {str(e)}",
                'workflow_id': workflow_id
            }, request_id=message.request_id, token=token, message_type="response")
            
            # Supprimer la requête en attente si elle existe
            delete_pending_request(message.request_id)

        except Exception as inner_e:
            logger.error(f"Erreur lors de l'envoi de la réponse d'erreur: {inner_e}")


def workflow_stop_handler(channel: str, message: Message):
    """
    Gestionnaire pour arrêter un workflow en cours d'exécution.

    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
    """
    try:
        logger.info(f"Demande d'arrêt de workflow reçue: {message.to_dict()}")

        # Extraire les données du message
        data = message.data
        request_id = message.request_id

        workflow_id = data.get('workflow_id')
        if not workflow_id:
            raise ValueError("workflow_id manquant dans la requête")

        # Récupérer le workflow
        from manager.models import Workflow, Task
        try:
            workflow = Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist:
            raise ValueError(f"Workflow {workflow_id} non trouvé")

        # Vérifier que le workflow peut être arrêté
        stoppable_statuses = ['RUNNING', 'PENDING', 'ASSIGNING', 'SPLITTING']
        if workflow.status not in stoppable_statuses:
            raise ValueError(f"Le workflow ne peut pas être arrêté (statut actuel: {workflow.status})")

        # Sauvegarder l'ancien statut
        old_status = workflow.status

        # Mettre à jour le statut du workflow
        workflow.status = 'PAUSED'
        workflow.updated_at = datetime.now(dt_timezone.utc)
        workflow.save()

        # Arrêter toutes les tâches en cours
        tasks = Task.objects.filter(workflow=workflow, status__in=['RUNNING', 'ASSIGNED'])
        stopped_tasks = []
        for task in tasks:
            task.status = 'PAUSED'
            task.save()
            stopped_tasks.append(str(task.id))

        logger.info(f"Workflow {workflow_id} arrêté avec succès ({len(stopped_tasks)} tâches arrêtées)")

        # Envoyer une réponse de succès
        client = RedisClient.get_instance()
        from .utils import get_coordinator_token
        token = get_coordinator_token()
        client.publish('workflow/stop_response', {
            'status': 'success',
            'message': f'Workflow {workflow.name} arrêté avec succès',
            'workflow_id': str(workflow.id),
            'old_status': old_status,
            'new_status': 'PAUSED',
            'stopped_tasks': stopped_tasks
        }, request_id=request_id, token=token, message_type="response")

    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt du workflow: {e}")
        logger.error(traceback.format_exc())

        try:
            client = RedisClient.get_instance()
            from .utils import get_coordinator_token
            token = get_coordinator_token()
            client.publish('workflow/stop_response', {
                'status': 'error',
                'message': str(e),
                'workflow_id': data.get('workflow_id', 'inconnu')
            }, request_id=message.request_id, token=token, message_type="response")
        except Exception as inner_e:
            logger.error(f"Erreur lors de l'envoi de la réponse d'erreur: {inner_e}")


def workflow_resume_handler(channel: str, message: Message):
    """
    Gestionnaire pour reprendre l'exécution d'un workflow en pause.

    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
    """
    try:
        logger.info(f"Demande de reprise de workflow reçue: {message.to_dict()}")

        # Extraire les données du message
        data = message.data
        request_id = message.request_id

        workflow_id = data.get('workflow_id')
        if not workflow_id:
            raise ValueError("workflow_id manquant dans la requête")

        # Récupérer le workflow
        from manager.models import Workflow, Task
        try:
            workflow = Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist:
            raise ValueError(f"Workflow {workflow_id} non trouvé")

        # Vérifier que le workflow est en pause
        if workflow.status != 'PAUSED':
            raise ValueError(f"Le workflow n'est pas en pause (statut actuel: {workflow.status})")

        # Mettre à jour le statut du workflow
        workflow.status = 'RUNNING'
        workflow.updated_at = datetime.now(dt_timezone.utc)
        workflow.save()

        # Reprendre toutes les tâches en pause
        tasks = Task.objects.filter(workflow=workflow, status='PAUSED')
        resumed_tasks = []
        for task in tasks:
            # Si la tâche avait démarré, la remettre en RUNNING, sinon en ASSIGNED
            if task.start_time:
                task.status = 'RUNNING'
            else:
                task.status = 'ASSIGNED'
            task.save()
            resumed_tasks.append({'id': str(task.id), 'status': task.status})

        logger.info(f"Workflow {workflow_id} repris avec succès ({len(resumed_tasks)} tâches reprises)")

        # Envoyer une réponse de succès
        client = RedisClient.get_instance()
        from .utils import get_coordinator_token
        token = get_coordinator_token()
        client.publish('workflow/resume_response', {
            'status': 'success',
            'message': f'Workflow {workflow.name} repris avec succès',
            'workflow_id': str(workflow.id),
            'new_status': 'RUNNING',
            'resumed_tasks': resumed_tasks
        }, request_id=request_id, token=token, message_type="response")

    except Exception as e:
        logger.error(f"Erreur lors de la reprise du workflow: {e}")
        logger.error(traceback.format_exc())

        try:
            client = RedisClient.get_instance()
            from .utils import get_coordinator_token
            token = get_coordinator_token()
            client.publish('workflow/resume_response', {
                'status': 'error',
                'message': str(e),
                'workflow_id': data.get('workflow_id', 'inconnu')
            }, request_id=message.request_id, token=token, message_type="response")
        except Exception as inner_e:
            logger.error(f"Erreur lors de l'envoi de la réponse d'erreur: {inner_e}")


def workflow_update_handler(channel: str, message: Message):
    """
    Gestionnaire pour mettre à jour un workflow.

    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
    """
    try:
        logger.info(f"Demande de mise à jour de workflow reçue: {message.to_dict()}")

        # Extraire les données du message
        data = message.data
        request_id = message.request_id

        workflow_id = data.get('workflow_id')
        if not workflow_id:
            raise ValueError("workflow_id manquant dans la requête")

        updates = data.get('updates', {})
        if not updates:
            raise ValueError("Aucune mise à jour fournie")

        # Récupérer le workflow
        from manager.models import Workflow
        try:
            workflow = Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist:
            raise ValueError(f"Workflow {workflow_id} non trouvé")

        # Sauvegarder l'ancien statut
        old_status = workflow.status

        # Appliquer les mises à jour
        updated_fields = []
        for field, value in updates.items():
            if hasattr(workflow, field):
                setattr(workflow, field, value)
                updated_fields.append(field)

        workflow.updated_at = datetime.now(dt_timezone.utc)
        workflow.save()

        logger.info(f"Workflow {workflow_id} mis à jour avec succès (champs: {', '.join(updated_fields)})")

        # Envoyer une réponse de succès
        client = RedisClient.get_instance()
        from .utils import get_coordinator_token
        token = get_coordinator_token()
        client.publish('workflow/update_response', {
            'status': 'success',
            'message': f'Workflow {workflow.name} mis à jour avec succès',
            'workflow_id': str(workflow.id),
            'updated_fields': updated_fields,
            'old_status': old_status,
            'new_status': workflow.status
        }, request_id=request_id, token=token, message_type="response")

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du workflow: {e}")
        logger.error(traceback.format_exc())

        try:
            client = RedisClient.get_instance()
            from .utils import get_coordinator_token
            token = get_coordinator_token()
            client.publish('workflow/update_response', {
                'status': 'error',
                'message': str(e),
                'workflow_id': data.get('workflow_id', 'inconnu')
            }, request_id=message.request_id, token=token, message_type="response")
        except Exception as inner_e:
            logger.error(f"Erreur lors de l'envoi de la réponse d'erreur: {inner_e}")


def workflow_delete_handler(channel: str, message: Message):
    """
    Gestionnaire pour supprimer un workflow.

    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
    """
    try:
        logger.info(f"Demande de suppression de workflow reçue: {message.to_dict()}")

        # Extraire les données du message
        data = message.data
        request_id = message.request_id

        workflow_id = data.get('workflow_id')
        if not workflow_id:
            raise ValueError("workflow_id manquant dans la requête")

        # Récupérer le workflow
        from manager.models import Workflow
        try:
            workflow = Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist:
            raise ValueError(f"Workflow {workflow_id} non trouvé")

        workflow_name = workflow.name

        # Supprimer le workflow (les tâches seront supprimées en cascade)
        workflow.delete()

        logger.info(f"Workflow {workflow_id} ({workflow_name}) supprimé avec succès")

        # Envoyer une réponse de succès
        client = RedisClient.get_instance()
        from .utils import get_coordinator_token
        token = get_coordinator_token()
        client.publish('workflow/delete_response', {
            'status': 'success',
            'message': f'Workflow {workflow_name} supprimé avec succès',
            'workflow_id': str(workflow_id)
        }, request_id=request_id, token=token, message_type="response")

    except Exception as e:
        logger.error(f"Erreur lors de la suppression du workflow: {e}")
        logger.error(traceback.format_exc())

        try:
            client = RedisClient.get_instance()
            from .utils import get_coordinator_token
            token = get_coordinator_token()
            client.publish('workflow/delete_response', {
                'status': 'error',
                'message': str(e),
                'workflow_id': data.get('workflow_id', 'inconnu')
            }, request_id=message.request_id, token=token, message_type="response")
        except Exception as inner_e:
            logger.error(f"Erreur lors de l'envoi de la réponse d'erreur: {inner_e}")
