"""
Gestionnaires pour les événements de statut et progression des tâches.
"""

import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Any

from volunteer.models import Volunteer
from redis_communication.message import Message
from redis_communication.volunteer_performance_handlers import update_volunteer_score
from manager.models import Task, TaskAssignment

logger = logging.getLogger(__name__)

def handle_task_created(channel: str, message: Message):
    """
    Gestionnaire pour l'événement de création d'une tâche par le Manager.
    Stocke la tâche dans la base de données du Coordinator.
    """
    try:
        data = message.data
        task_id = data.get('task_id')
        workflow_id = data.get('workflow_id')
        task_name = data.get('name', f'Task-{task_id}')

        if not task_id or not workflow_id:
            logger.error(f"Task ID ou Workflow ID manquant dans task/created: {data}")
            return

        # Vérifier si la tâche existe déjà
        existing_task = Task.objects.filter(id=task_id).first()
        if existing_task:
            logger.info(f"Tâche {task_id} existe déjà, mise à jour")
            existing_task.name = task_name
            existing_task.status = data.get('status', 'PENDING')
            existing_task.command = data.get('command', '')
            existing_task.save()
            return

        # Récupérer le workflow
        from manager.models import Workflow
        try:
            workflow = Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist:
            logger.error(f"Workflow {workflow_id} non trouvé pour la tâche {task_id}")
            return

        # Créer la tâche
        task = Task(
            id=task_id,
            name=task_name,
            workflow=workflow,
            status=data.get('status', 'PENDING'),
            command=data.get('command', ''),
            description=data.get('description', ''),
            required_resources=data.get('required_resources', {}),
            input_files=data.get('input_files', []),
            output_files=data.get('output_files', []),
        )
        task.save()

        logger.info(f"Tâche {task_id} ({task_name}) créée pour le workflow {workflow_id}")

    except Exception as e:
        logger.error(f"Erreur lors de la création de la tâche: {e}")
        logger.error(traceback.format_exc())


def handle_task_started(channel: str, message: Message):
    """
    Gestionnaire pour l'événement de démarrage d'une tâche.
    """
    try:
        data = message.data
        task_id = data.get('task_id')
        volunteer_id = data.get('volunteer_id')

        if not task_id or not volunteer_id:
            logger.error("Task ID ou Volunteer ID manquant")
            return

        # Mettre à jour l'assignation
        assignment = TaskAssignment.objects.get(
            task=task_id,
            volunteer=volunteer_id,
            status='ASSIGNED'
        )
        assignment.status = 'STARTED'
        assignment.started_at = datetime.now(timezone.utc)
        assignment.save()

        # Mettre à jour la tâche
        task = Task.objects.get(id=task_id)
        task.status = 'RUNNING'
        task.start_time = datetime.now(timezone.utc)
        task.save()

        logger.info(f"Tâche {task_id} démarrée par le volontaire {volunteer_id}")

    except Exception as e:
        logger.error(f"Erreur lors du traitement du démarrage de la tâche: {e}")
        logger.error(traceback.format_exc())

def handle_task_progress(channel: str, message: Message):
    """
    Gère la mise à jour du progrès d'une tâche
    """
    try:
        data = message.data
        task_id = data.get('task_id')
        volunteer_id = data.get('volunteer_id')
        progress = data.get('progress', 0)
        
        # Vérifier les données requises
        if not all([task_id, volunteer_id]):
            logger.error("Données manquantes dans le message de progression")
            return
            
        try:
            # Rechercher l'assignation
            assignment = TaskAssignment.objects.get(
                task=task_id,
                volunteer=volunteer_id,
                status__in=['ASSIGNED', 'STARTED', 'RESUMED']  # Ajout des états valides
            )
            
            # Mettre à jour le progrès
            assignment.progress = progress
            if progress > 0 and assignment.status == 'ASSIGNED':
                assignment.status = 'STARTED'
                assignment.started_at = datetime.now(timezone.utc)
            assignment.save()
            
            # Mettre à jour la tâche elle-même
            task = assignment.task
            task.progress = progress
            task.save()
            
            logger.info(f"Progression mise à jour - Tâche: {task_id}, Progrès: {progress}%")
            
        except TaskAssignment.DoesNotExist:
            # Créer une nouvelle assignation si elle n'existe pas
            logger.warning(f"Assignation non trouvée pour tâche={task_id}, volontaire={volunteer_id}")
            try:
                task = Task.objects.get(id=task_id)
                volunteer = Volunteer.objects.get(id=volunteer_id)
                
                assignment = TaskAssignment(
                    task=task,
                    volunteer=volunteer,
                    status='STARTED',
                    progress=progress,
                    started_at=datetime.now(timezone.utc)
                )
                assignment.save()
                
                # Mettre à jour la tâche
                task.progress = progress
                task.assigned_to = volunteer
                task.save()
                
                logger.info(f"Nouvelle assignation créée pour la tâche {task_id}")
                
            except (Task.DoesNotExist, Volunteer.DoesNotExist) as e:
                logger.error(f"Impossible de créer l'assignation: {str(e)}")
                return
                
    except Exception as e:
        import traceback
        logger.error(f"Erreur lors du traitement du progrès: {str(e)}")
        logger.error(traceback.format_exc())

def handle_task_completed(channel: str, message: Message):
    """
    Gestionnaire pour la complétion des tâches.
    """
    try:
        data = message.data
        task_id = data.get('task_id')
        volunteer_id = data.get('volunteer_id')
        results = data.get('results', {})

        if not all([task_id, volunteer_id]):
            logger.error("Données manquantes dans la notification de complétion")
            return

        now = datetime.now(timezone.utc)

        # Mettre à jour l'assignation
        assignment = TaskAssignment.objects.get(
            task=task_id,
            volunteer=volunteer_id,
            status__in=['STARTED', 'RESUMED']
        )
        assignment.status = 'COMPLETED'
        assignment.completed_at = now
        assignment.progress = 100
        if assignment.started_at:
            assignment.completion_time = (now - assignment.started_at).total_seconds()
        assignment.save()

        # Mettre à jour la tâche
        task = Task.objects.get(id=task_id)
        task.status = 'COMPLETED'
        task.progress = 100
        task.end_time = now
        task.results = results
        task.save()

        # Mettre à jour le score du volontaire
        update_volunteer_score(volunteer_id, 'completed', task_id)

        logger.info(f"Tâche {task_id} terminée avec succès par le volontaire {volunteer_id}")

    except Exception as e:
        logger.error(f"Erreur lors du traitement de la complétion de la tâche: {e}")
        logger.error(traceback.format_exc())

def handle_task_failed(channel: str, message: Message):
    """
    Gestionnaire pour les échecs de tâches.
    """
    try:
        data = message.data
        task_id = data.get('task_id')
        volunteer_id = data.get('volunteer_id')
        error = data.get('error')

        if not all([task_id, volunteer_id]):
            logger.error("Données manquantes dans la notification d'échec")
            return

        # Mettre à jour l'assignation
        assignment = TaskAssignment.objects.get(
            task=task_id,
            volunteer=volunteer_id,
            status__in=['STARTED', 'RESUMED']
        )
        assignment.status = 'FAILED'
        assignment.completed_at = datetime.now(timezone.utc)
        assignment.failure_reason = error
        assignment.save()

        # Mettre à jour la tâche
        task = Task.objects.get(id=task_id)
        task.status = 'FAILED'
        task.end_time = datetime.now(timezone.utc)
        task.error_details = {'error': error, 'volunteer_id': str(volunteer_id)}
        task.attempts += 1
        task.save()

        # Mettre à jour le score du volontaire
        update_volunteer_score(volunteer_id, 'failed', task_id)

        logger.error(f"Tâche {task_id} échouée par le volontaire {volunteer_id}: {error}")

    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'échec de la tâche: {e}")
        logger.error(traceback.format_exc())

def handle_task_paused(channel: str, message: Message):
    """
    Gestionnaire pour la mise en pause des tâches.
    """
    try:
        data = message.data
        task_id = data.get('task_id')
        volunteer_id = data.get('volunteer_id')

        if not all([task_id, volunteer_id]):
            logger.error("Données manquantes dans la notification de pause")
            return

        # Mettre à jour l'assignation
        assignment = TaskAssignment.objects.get(
            task=task_id,
            volunteer=volunteer_id,
            status__in=['STARTED', 'RESUMED']
        )
        assignment.status = 'PAUSED'
        assignment.save()

        # Mettre à jour la tâche 
        task = Task.objects.get(id=task_id)
        task.status = 'PAUSED'
        task.save()

        logger.info(f"Tâche {task_id} mise en pause par le volontaire {volunteer_id}")

    except Exception as e:
        logger.error(f"Erreur lors du traitement de la pause de la tâche: {e}")
        logger.error(traceback.format_exc())

def handle_task_resumed(channel: str, message: Message):
    """
    Gestionnaire pour la reprise des tâches.
    """
    try:
        data = message.data
        task_id = data.get('task_id')
        volunteer_id = data.get('volunteer_id')

        if not all([task_id, volunteer_id]):
            logger.error("Données manquantes dans la notification de reprise")
            return

        # Mettre à jour l'assignation
        assignment = TaskAssignment.objects.get(
            task=task_id,
            volunteer=volunteer_id,
            status='PAUSED'
        )
        assignment.status = 'RESUMED'
        assignment.save()

        # Mettre à jour la tâche
        task = Task.objects.get(id=task_id)
        task.status = 'RUNNING'
        task.save()

        logger.info(f"Tâche {task_id} reprise par le volontaire {volunteer_id}")

    except Exception as e:
        logger.error(f"Erreur lors du traitement de la reprise de la tâche: {e}")
        logger.error(traceback.format_exc())

def handle_task_timeout(channel: str, message: Message):
    """
    Gestionnaire pour les timeouts de tâches.
    """
    try:
        data = message.data
        task_id = data.get('task_id')
        volunteer_id = data.get('volunteer_id')

        if not all([task_id, volunteer_id]):
            logger.error("Données manquantes dans la notification de timeout")
            return

        # Mettre à jour l'assignation
        assignment = TaskAssignment.objects.get(
            task=task_id,
            volunteer=volunteer_id,
            status__in=['STARTED', 'RESUMED']
        )
        assignment.status = 'TIMEOUT'
        assignment.completed_at = datetime.now(timezone.utc)
        assignment.failure_reason = "Task execution timeout"
        assignment.save()

        # Mettre à jour la tâche
        task = Task.objects.get(id=task_id)
        task.status = 'FAILED'
        task.end_time = datetime.now(timezone.utc)
        task.error_details = {
            'error': 'Task execution timeout',
            'volunteer_id': str(volunteer_id)
        }
        task.attempts += 1
        task.save()

        # Mettre à jour le score du volontaire
        update_volunteer_score(volunteer_id, 'timeout', task_id)

        logger.warning(f"Timeout pour la tâche {task_id} sur le volontaire {volunteer_id}")

    except Exception as e:
        logger.error(f"Erreur lors du traitement du timeout de la tâche: {e}")
        logger.error(traceback.format_exc())

def handle_task_status(channel: str, message: Message):
    """
    Handler unifié pour les messages task/status.
    Dispatch vers le bon handler selon le statut contenu dans le message.
    """
    try:
        data = message.data
        status = data.get('status', '').lower()
        task_id = data.get('task_id')
        volunteer_id = data.get('volunteer_id')
        workflow_id = data.get('workflow_id')

        logger.info(f"[task/status] Reçu statut '{status}' pour tâche {task_id} du volontaire {volunteer_id}")

        if not task_id:
            logger.error("Task ID manquant dans le message task/status")
            return

        # Mapper le statut vers le bon handler
        if status == 'completed':
            # Gérer les fichiers de sortie si présents
            file_server = data.get('file_server', {})
            if file_server:
                logger.info(f"Fichiers de sortie disponibles: {file_server}")
                _handle_task_output_files(task_id, volunteer_id, workflow_id, file_server, data)
            handle_task_completed(channel, message)

        elif status in ['failed', 'error']:
            handle_task_failed(channel, message)

        elif status == 'paused':
            handle_task_paused(channel, message)

        elif status in ['progress', 'running']:
            handle_task_started(channel, message)

        elif status == 'resumed':
            handle_task_resumed(channel, message)

        elif status == 'cancel':
            # Traiter comme un échec
            data['error'] = data.get('error', 'Tâche annulée')
            handle_task_failed(channel, message)

        else:
            logger.warning(f"Statut inconnu '{status}' pour la tâche {task_id}")

    except Exception as e:
        logger.error(f"Erreur dans handle_task_status: {e}")
        logger.error(traceback.format_exc())


def _handle_task_output_files(task_id: str, volunteer_id: str, workflow_id: str, file_server: dict, data: dict):
    """
    Télécharge les fichiers de sortie depuis le serveur de fichiers du volontaire
    et les transfère vers le manager.
    """
    import requests
    import os

    try:
        host = file_server.get('host')
        port = file_server.get('port')
        path = file_server.get('path', '/files/')
        output_files = file_server.get('output_files', [])

        if not host or not port:
            logger.warning(f"Informations serveur de fichiers incomplètes pour la tâche {task_id}")
            return

        base_url = f"http://{host}:{port}{path}"
        logger.info(f"Téléchargement des fichiers depuis {base_url}")

        # Créer le répertoire de destination
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'task_outputs', str(task_id))
        os.makedirs(output_dir, exist_ok=True)

        downloaded_files = []
        for filename in output_files:
            try:
                file_url = f"{base_url}{filename}"
                logger.info(f"Téléchargement de {file_url}")

                response = requests.get(file_url, timeout=60, stream=True)
                response.raise_for_status()

                local_path = os.path.join(output_dir, filename)
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                downloaded_files.append(filename)
                logger.info(f"Fichier {filename} téléchargé avec succès")

            except Exception as e:
                logger.error(f"Erreur lors du téléchargement de {filename}: {e}")

        # Transférer les fichiers vers le manager via Redis
        if downloaded_files and workflow_id:
            from .client import RedisClient
            from django.conf import settings
            client = RedisClient.get_instance()

            coordinator_host = getattr(settings, 'COORDINATOR_PUBLIC_HOST', '173.249.38.251')
            coordinator_port = getattr(settings, 'COORDINATOR_PORT', 8001)

            # Notifier le manager que les fichiers sont prêts (canal générique)
            client.publish('manager/task_files', {
                'task_id': task_id,
                'workflow_id': workflow_id,
                'volunteer_id': volunteer_id,
                'status': 'files_ready',
                'files': downloaded_files,
                'output_dir': output_dir,
                'file_server': {
                    'coordinator_host': coordinator_host,
                    'coordinator_port': coordinator_port,
                    'path': f'/api/task-outputs/{task_id}/'
                }
            })
            logger.info(f"Notification envoyée au manager pour {len(downloaded_files)} fichiers")

    except Exception as e:
        logger.error(f"Erreur dans _handle_task_output_files: {e}")
        logger.error(traceback.format_exc())


def register_handlers(client):
    """
    Enregistre les gestionnaires d'événements pour le statut des tâches.
    """
    client.subscribe('task/created', handle_task_created)
    client.subscribe('task/started', handle_task_started)
    client.subscribe('task/progress', handle_task_progress)
    client.subscribe('task/completed', handle_task_completed)
    client.subscribe('task/failed', handle_task_failed)
    client.subscribe('task/paused', handle_task_paused)
    client.subscribe('task/resumed', handle_task_resumed)
    client.subscribe('task/timeout', handle_task_timeout)
    # Handler unifié pour task/status (utilisé par les volontaires)
    client.subscribe('task/status', handle_task_status)

    logger.info("Gestionnaires de statut des tâches enregistrés (incluant task/status)")