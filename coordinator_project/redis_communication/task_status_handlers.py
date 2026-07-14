"""
Gestionnaires pour les événements de statut et progression des tâches.
"""

import logging
import traceback
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from volunteer.models import Volunteer
from redis_communication.message import Message
from redis_communication.volunteer_performance_handlers import update_volunteer_score
from manager.models import Task, TaskAssignment, Workflow
from redis_communication.volunteer_matching import ACTIVE_ASSIGNMENT_STATUSES

logger = logging.getLogger(__name__)

_TERMINAL_TASK_STATUSES = frozenset({'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT'})
_TERMINAL_ASSIGNMENT_STATUSES = frozenset({'COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED'})

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def _notify_frontend(event_type, data):
    """
    Envoie une notification via WebSocket au frontend.
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "tasks_updates",
                {
                    "type": event_type,
                    **data
                }
            )
            logger.debug(f"Notification WS envoyée: {event_type} pour {data.get('task_id', 'unknown')}")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la notification WS: {e}")

def _apply_task_payload(task, data: Dict[str, Any]) -> None:
    """Applique les métadonnées reçues du Manager sur une tâche Coordinateur."""
    task.name = data.get('name', task.name)
    task.command = data.get('command', task.command or '')
    task.description = data.get('description', task.description or '')
    task.required_resources = data.get('required_resources', task.required_resources or {})
    if task.status not in _TERMINAL_TASK_STATUSES:
        incoming = _parse_progress(data.get('progress'), task.progress or 0)
        task.progress = max(float(task.progress or 0), incoming)
    elif str(task.status).upper() == 'COMPLETED':
        task.progress = 100.0
    if data.get('parameters') is not None:
        task.parameters = data.get('parameters') or []
    if data.get('dependencies') is not None:
        task.dependencies = data.get('dependencies') or []
    if data.get('is_subtask') is not None:
        task.is_subtask = bool(data.get('is_subtask'))
    if data.get('estimated_execution_time') is not None:
        task.estimated_execution_time = float(data.get('estimated_execution_time') or 0)
    if data.get('input_data'):
        task.input_data = data.get('input_data') or {}
    if data.get('input_data_size') is not None:
        task.input_data_size = float(data.get('input_data_size') or 0)
    if data.get('docker_information'):
        task.docker_information = dict(data.get('docker_information') or {})
    meta = dict(task.metadata or {})
    if data.get('input_files') is not None:
        meta['input_files'] = data.get('input_files') or []
    if data.get('output_files') is not None:
        meta['output_files'] = data.get('output_files') or []
    if data.get('workflow_type'):
        meta['workflow_type'] = data.get('workflow_type')
    task.metadata = meta


def _trigger_coordinator_assignment() -> None:
    """Lance l'assignation en arrière-plan (évite de bloquer le handler Redis)."""
    import threading

    def _run():
        try:
            from redis_communication.task_assigner import run_coordinator_assignment_cycle
            result = run_coordinator_assignment_cycle()
            logger.info("Assignation coordinateur: %s", result.get("message"))
        except Exception as exc:
            logger.warning("Assignation coordinateur échouée: %s", exc)

    threading.Thread(target=_run, daemon=True, name="coord-assign").start()


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

        # Normaliser les statuts Manager -> Coordinateur
        status = str(data.get('status', 'PENDING')).upper()
        status_map = {
            'CREATED': 'PENDING',
            'PENDING': 'PENDING',
            'ASSIGNED': 'ASSIGNED',
            'RUNNING': 'RUNNING',
            'STARTED': 'RUNNING',
            'COMPLETED': 'COMPLETED',
            'FAILED': 'FAILED',
        }
        coord_status = status_map.get(status, 'PENDING')

        # Vérifier si la tâche existe déjà
        existing_task = Task.objects.filter(id=task_id).first()
        if existing_task:
            logger.info(f"Tâche {task_id} existe déjà, mise à jour")
            existing_task.status = coord_status
            _apply_task_payload(existing_task, data)
            existing_task.save()
            if coord_status == 'PENDING':
                _trigger_coordinator_assignment()
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
            status=coord_status,
            command=data.get('command', ''),
            description=data.get('description', ''),
            required_resources=data.get('required_resources', {}),
            progress=float(data.get('progress') or 0),
            parameters=data.get('parameters', []),
            dependencies=data.get('dependencies', []),
            is_subtask=bool(data.get('is_subtask', False)),
            estimated_execution_time=float(data.get('estimated_execution_time') or 0),
            input_data=data.get('input_data') or {},
            input_data_size=float(data.get('input_data_size') or 0),
            docker_information=dict(data.get('docker_information') or {}),
            metadata={
                'input_files': data.get('input_files') or [],
                'output_files': data.get('output_files') or [],
                'workflow_type': data.get('workflow_type') or getattr(workflow, 'workflow_type', ''),
            },
        )
        task.save()

        # Mettre à jour le compteur implicite: statut workflow au moins PENDING/RUNNING
        if workflow.status in ('CREATED', None, ''):
            workflow.status = 'PENDING'
            workflow.save()

        # Notifier le frontend
        _notify_frontend('task_created', {
            'task': {
                'id': str(task.id),
                'name': task.name,
                'status': task.status,
                'workflow': str(workflow.id)
            }
        })

        logger.info(f"Tâche {task_id} ({task_name}) créée pour le workflow {workflow_id}")
        _trigger_coordinator_assignment()

    except Exception as e:
        logger.error(f"Erreur lors de la création de la tâche: {e}")
        logger.error(traceback.format_exc())


def _parse_progress(value, default=0.0) -> float:
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return float(default or 0)


def _progress_for_status(status: str, progress: float) -> float:
    """COMPLETED impose toujours 100 % — évite les régressions après complétion."""
    if str(status or '').upper() == 'COMPLETED':
        return 100.0
    return _parse_progress(progress, 0)


def _get_task(task_id):
    return Task.objects.filter(id=task_id).first()


def _get_assignment(task_id, volunteer_id):
    """Retrouve l'assignation active (ASSIGNED/STARTED/RESUMED), sinon la plus récente."""
    qs = TaskAssignment.objects.filter(task=task_id)
    if volunteer_id:
        qs = qs.filter(volunteer=volunteer_id)
    active = qs.filter(status__in=('ASSIGNED', 'STARTED', 'RESUMED')).order_by('-assigned_at').first()
    if active:
        return active
    return qs.order_by('-assigned_at').first()


def _close_active_assignments_for_task(task, *, keep_id=None, now=None):
    """Libère tous les créneaux actifs d'une tâche (évite les STARTED fantômes qui bloquent la file)."""
    now = now or datetime.now(timezone.utc)
    for assignment in TaskAssignment.objects(task=task, status__in=('ASSIGNED', 'STARTED', 'RESUMED')):
        if keep_id is not None and str(assignment.id) == str(keep_id):
            continue
        assignment.status = 'CANCELLED'
        assignment.completed_at = now
        assignment.save()


def _sync_workflow_status(workflow: Workflow | None) -> None:
    """Recalcule le statut workflow depuis les tâches pour éviter les divergences d'UI."""
    if not workflow:
        return
    tasks = Task.objects(workflow=workflow)
    total = tasks.count()
    if total == 0:
        if workflow.status != 'PENDING':
            workflow.status = 'PENDING'
            workflow.save()
        return

    completed = tasks.filter(status='COMPLETED').count()
    failed = tasks.filter(status='FAILED').count()
    active = tasks.filter(status__in=['ASSIGNED', 'RUNNING']).count()
    pending = tasks.filter(status__in=['PENDING', 'CREATED']).count()

    next_status = workflow.status
    if completed >= total:
        next_status = 'COMPLETED'
    elif active > 0:
        next_status = 'RUNNING'
    elif failed > 0 and pending == 0:
        next_status = 'FAILED'
    else:
        next_status = 'PENDING'

    if workflow.status != next_status:
        workflow.status = next_status
        workflow.save()


def handle_task_started(channel: str, message: Message):
    """
    Gestionnaire pour l'événement de démarrage d'une tâche.
    """
    try:
        data = message.data
        task_id = data.get('task_id')
        volunteer_id = data.get('volunteer_id')
        progress = _parse_progress(data.get('progress'), 0)

        if not task_id:
            logger.error("Task ID manquant")
            return

        task = _get_task(task_id)
        if not task:
            logger.error(f"Tâche {task_id} introuvable pour démarrage")
            return

        if task.status in _TERMINAL_TASK_STATUSES:
            logger.debug("Démarrage ignoré pour tâche terminale %s", task_id)
            return

        old_status = task.status
        task.status = 'RUNNING'
        if not task.start_time:
            task.start_time = datetime.now(timezone.utc)
        task.progress = max(float(task.progress or 0), progress)
        task.save()

        assignment = _get_assignment(task_id, volunteer_id)
        if assignment and assignment.status not in _TERMINAL_ASSIGNMENT_STATUSES:
            if assignment.status in ('ASSIGNED',):
                assignment.status = 'STARTED'
            if not assignment.started_at:
                assignment.started_at = datetime.now(timezone.utc)
            assignment.progress = max(float(assignment.progress or 0), progress)
            assignment.save()
        elif volunteer_id:
            try:
                volunteer = Volunteer.objects.get(id=volunteer_id)
                TaskAssignment(
                    task=task,
                    volunteer=volunteer,
                    status='STARTED',
                    progress=progress,
                    started_at=datetime.now(timezone.utc),
                ).save()
            except Volunteer.DoesNotExist:
                logger.warning(f"Volontaire {volunteer_id} introuvable pour démarrage tâche {task_id}")

        _notify_frontend('task_status_changed', {
            'task_id': str(task_id),
            'task_name': task.name,
            'old_status': old_status,
            'new_status': 'RUNNING',
            'progress': task.progress,
        })

        logger.info(f"Tâche {task_id} démarrée par le volontaire {volunteer_id}")

    except Exception as e:
        logger.error(f"Erreur lors du traitement du démarrage de la tâche: {e}")
        logger.error(traceback.format_exc())

def handle_task_progress(channel: str, message: Message):
    """
    Gère la mise à jour du progrès d'une tâche (source de vérité partagée).
    """
    try:
        data = message.data or {}
        task_id = data.get('task_id')
        volunteer_id = data.get('volunteer_id')
        progress = _parse_progress(data.get('progress'), 0)

        if not task_id:
            logger.error("Données manquantes dans le message de progression")
            return

        task = _get_task(task_id)
        if not task:
            logger.error(f"Tâche {task_id} introuvable pour progression")
            return

        if task.status in _TERMINAL_TASK_STATUSES:
            logger.debug("Progression ignorée pour tâche terminale %s (statut %s)", task_id, task.status)
            return

        old_status = task.status
        task.progress = max(float(task.progress or 0), progress)
        if progress > 0 and task.status in ('PENDING', 'ASSIGNED', 'CREATED'):
            task.status = 'RUNNING'
            if not task.start_time:
                task.start_time = datetime.now(timezone.utc)
        task.save()

        assignment = _get_assignment(task_id, volunteer_id)
        if assignment and assignment.status not in _TERMINAL_ASSIGNMENT_STATUSES:
            assignment.progress = max(float(assignment.progress or 0), progress)
            if progress > 0 and assignment.status == 'ASSIGNED':
                assignment.status = 'STARTED'
                if not assignment.started_at:
                    assignment.started_at = datetime.now(timezone.utc)
            assignment.save()
        elif volunteer_id:
            try:
                volunteer = Volunteer.objects.get(id=volunteer_id)
                TaskAssignment(
                    task=task,
                    volunteer=volunteer,
                    status='STARTED',
                    progress=progress,
                    started_at=datetime.now(timezone.utc),
                ).save()
                task.assigned_to = volunteer
                task.save()
            except Volunteer.DoesNotExist:
                logger.warning(
                    "Progression tâche %s: volontaire %s inconnu (Task.progress=%s)",
                    task_id, volunteer_id, progress,
                )

        # Si le volontaire envoie 100% sans message completed, cloturer quand meme.
        if float(progress) >= 99.5 and str(task.status or '').upper() not in _TERMINAL_TASK_STATUSES:
            logger.info(
                "Progression 100%% sans completed → auto-complete tâche %s",
                task_id,
            )
            fake = Message(
                request_id=getattr(message, 'request_id', None) or str(uuid.uuid4()),
                sender=getattr(message, 'sender', {}) or {'type': 'system', 'id': 'coordinator'},
                message_type='event',
                data={
                    'task_id': task_id,
                    'volunteer_id': volunteer_id,
                    'results': data.get('results') or {},
                },
            )
            handle_task_completed(channel, fake)
            return

        logger.info("Progression synchronisée — tâche %s: %s%%", task_id, progress)

        _notify_frontend('task_status_changed', {
            'task_id': str(task_id),
            'task_name': task.name,
            'old_status': old_status,
            'new_status': task.status,
            'progress': progress,
            'workflow_id': str(task.workflow.id) if task.workflow else None,
        })

    except Exception as e:
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
        results = data.get('results', {}) or data.get('file_server', {}) or {}

        if not task_id:
            logger.error("Données manquantes dans la notification de complétion")
            return

        now = datetime.now(timezone.utc)
        task = _get_task(task_id)
        if not task:
            logger.error(f"Tâche {task_id} introuvable pour complétion")
            return

        old_status = task.status
        task.status = 'COMPLETED'
        task.progress = 100
        task.end_time = now
        if results:
            task.results = results
        task.save()

        assignment = _get_assignment(task_id, volunteer_id)
        keep_id = None
        if assignment and str(assignment.status or '').upper() in ('ASSIGNED', 'STARTED', 'RESUMED', 'COMPLETED'):
            assignment.status = 'COMPLETED'
            assignment.completed_at = now
            assignment.progress = 100
            if assignment.started_at:
                assignment.completion_time = (now - assignment.started_at).total_seconds()
            assignment.save()
            keep_id = assignment.id
        elif volunteer_id:
            try:
                volunteer = Volunteer.objects.get(id=volunteer_id)
                created = TaskAssignment(
                    task=task,
                    volunteer=volunteer,
                    status='COMPLETED',
                    progress=100,
                    started_at=now,
                    completed_at=now,
                )
                created.save()
                keep_id = created.id
            except Volunteer.DoesNotExist:
                pass

        # Toujours libérer les créneaux actifs restants (STARTED orphelins / update mongoengine).
        _close_active_assignments_for_task(task, keep_id=keep_id, now=now)

        _notify_frontend('task_status_changed', {
            'task_id': str(task_id),
            'task_name': task.name,
            'old_status': old_status,
            'new_status': 'COMPLETED',
            'progress': 100,
        })

        if volunteer_id:
            update_volunteer_score(volunteer_id, 'completed', task_id)

        logger.info(f"Tâche {task_id} terminée avec succès par le volontaire {volunteer_id}")

        # Libérer le créneau → réassigner immédiatement aux autres volontaires libres
        _trigger_coordinator_assignment()

    except Exception as e:
        logger.error(f"Erreur lors du traitement de la complétion de la tâche: {e}")
        logger.error(traceback.format_exc())

def handle_task_failed(channel: str, message: Message):
    """
    Gestionnaire pour les échecs de tâches.
    Les refus de préférences remettent la tâche en file (PENDING).
    """
    try:
        data = message.data or {}
        task_id = data.get('task_id')
        volunteer_id = data.get('volunteer_id')
        error_type = str(data.get('error_type') or '').lower()
        error = data.get('error_message') or data.get('error') or ''

        if not all([task_id, volunteer_id]):
            logger.error("Données manquantes dans la notification d'échec")
            return

        assignment = TaskAssignment.objects.filter(
            task=task_id,
            volunteer=volunteer_id,
            status__in=['ASSIGNED', 'STARTED', 'RESUMED'],
        ).order_by('-assigned_at').first()

        task = Task.objects.filter(id=task_id).first()
        if not task:
            logger.warning("Tâche %s introuvable pour échec", task_id)
            return

        requeue = error_type in ('preference_mismatch', 'schedule', 'capacity')

        if requeue:
            if assignment:
                assignment.status = 'CANCELLED'
                assignment.failure_reason = error or error_type
                assignment.save()
            task.status = 'PENDING'
            task.assigned_to = None
            task.end_time = None
            task.error_details = {
                'last_reject': error or error_type,
                'error_type': error_type,
                'volunteer_id': str(volunteer_id),
            }
            task.save()
            _notify_frontend('task_status_changed', {
                'task_id': str(task.id),
                'task_name': task.name,
                'status': 'PENDING',
                'new_status': 'PENDING',
                'progress': float(task.progress or 0),
                'workflow_id': str(task.workflow.id) if task.workflow else None,
            })
            logger.info(
                "Tâche %s remise en file (%s): %s",
                task_id,
                error_type,
                error,
            )
            from redis_communication.task_status_handlers import (
                _trigger_coordinator_assignment,
            )
            _trigger_coordinator_assignment()
            return

        if assignment:
            assignment.status = 'FAILED'
            assignment.completed_at = datetime.now(timezone.utc)
            assignment.failure_reason = error
            assignment.save()

        task.status = 'FAILED'
        task.end_time = datetime.now(timezone.utc)
        task.error_details = {'error': error, 'volunteer_id': str(volunteer_id)}
        task.attempts = (task.attempts or 0) + 1
        task.save()

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
        if status == 'completed' or status == 'complete':
            # Toujours marquer COMPLETED d'abord — le fetch des sorties ne doit jamais bloquer ça.
            handle_task_completed(channel, message)
            file_server = data.get('file_server', {}) or {}
            # Si le volontaire a déjà uploadé vers le manager, rien à retélécharger.
            if file_server and not file_server.get('uploaded'):
                try:
                    logger.info(f"Fichiers de sortie disponibles: {file_server}")
                    _handle_task_output_files(task_id, volunteer_id, workflow_id, file_server, data)
                except Exception as fetch_exc:
                    logger.warning(
                        "Récupération sorties échouée pour %s (tâche déjà COMPLETED): %s",
                        task_id,
                        fetch_exc,
                    )

        elif status in ['failed', 'error']:
            handle_task_failed(channel, message)

        elif status == 'paused':
            handle_task_paused(channel, message)

        elif status in ['progress', 'running', 'started']:
            # Progression éventuelle dans le même message
            if data.get('progress') is not None:
                handle_task_progress(channel, message)
            else:
                handle_task_started(channel, message)

        elif status == 'resumed':
            handle_task_resumed(channel, message)

        elif status == 'cancel':
            # Traiter comme un échec
            data['error'] = data.get('error', 'Tâche annulée')
            handle_task_failed(channel, message)

        else:
            logger.warning(f"Statut inconnu '{status}' pour la tâche {task_id}")

        task = Task.objects(id=task_id).first()
        if task:
            _sync_workflow_status(task.workflow)

    except Exception as e:
        logger.error(f"Erreur dans handle_task_status: {e}")
        logger.error(traceback.format_exc())


def _handle_task_output_files(task_id: str, volunteer_id: str, workflow_id: str, file_server: dict, data: dict):
    """
    Télécharge les fichiers de sortie depuis le serveur de fichiers du volontaire
    et les transfère vers le manager.
    """
    try:
        import requests
    except ImportError:
        logger.warning(
            "Module requests absent — skip téléchargement sorties pour tâche %s",
            task_id,
        )
        return

    import os

    try:
        if file_server.get('uploaded'):
            logger.info("Sorties déjà uploadées par le volontaire pour %s — skip fetch LAN", task_id)
            return

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


def handle_task_status_sync(channel: str, message: Message):
    """
    Synchronise le statut d'une tâche depuis le Manager (file d'attente / assignation).
    """
    try:
        data = message.data or {}
        task_id = data.get('task_id')
        status = str(data.get('status') or '').upper()
        if not task_id or not status:
            return

        status_map = {
            'CREATED': 'PENDING',
            'PENDING': 'PENDING',
            'ASSIGNED': 'ASSIGNED',
            'RUNNING': 'RUNNING',
            'STARTED': 'RUNNING',
            'COMPLETED': 'COMPLETED',
            'FAILED': 'FAILED',
        }
        coord_status = status_map.get(status, status)

        task = Task.objects(id=task_id).first()
        if not task:
            logger.warning("task/status_sync: tâche %s introuvable", task_id)
            return

        prev = str(task.status or "").upper()
        # Ne jamais rétrograder COMPLETED/FAILED/… vers RUNNING/ASSIGNED/PENDING
        if prev in _TERMINAL_TASK_STATUSES and coord_status not in _TERMINAL_TASK_STATUSES:
            logger.info(
                "task/status_sync: ignore rétrogradation %s → %s pour tâche %s",
                prev,
                coord_status,
                task_id,
            )
            return

        task.status = coord_status
        if coord_status == 'COMPLETED':
            task.progress = 100.0
        elif data.get('progress') is not None and coord_status not in _TERMINAL_TASK_STATUSES:
            task.progress = max(float(task.progress or 0), float(data.get('progress') or 0))
        if data.get('name'):
            task.name = data['name']

        clear_assignment = bool(data.get('clear_assignment'))
        volunteer_id = data.get('volunteer_id')

        if clear_assignment or coord_status in ('PENDING', 'CREATED'):
            task.assigned_to = None
            TaskAssignment.objects(
                task=task,
                status__in=list(ACTIVE_ASSIGNMENT_STATUSES),
            ).update(status='CANCELLED')
        elif volunteer_id and coord_status in ('ASSIGNED', 'RUNNING'):
            volunteer = Volunteer.objects(id=volunteer_id).first()
            if volunteer:
                task.assigned_to = volunteer
                existing = TaskAssignment.objects(task=task, volunteer=volunteer, status__in=['ASSIGNED', 'STARTED']).first()
                if not existing:
                    TaskAssignment.objects(task=task, status='ASSIGNED').update(status='CANCELLED')
                    TaskAssignment(
                        task=task,
                        volunteer=volunteer,
                        status='STARTED' if coord_status == 'RUNNING' else 'ASSIGNED',
                        progress=float(task.progress or 0),
                        assigned_at=datetime.now(timezone.utc),
                        started_at=datetime.now(timezone.utc) if coord_status == 'RUNNING' else None,
                    ).save()

        task.save()

        workflow = task.workflow
        if workflow and coord_status in ('ASSIGNED', 'RUNNING') and workflow.status in ('CREATED', 'PENDING'):
            workflow.status = 'RUNNING'
            workflow.save()
        elif workflow and coord_status == 'COMPLETED':
            done = Task.objects(workflow=workflow, status='COMPLETED').count()
            total = Task.objects(workflow=workflow).count()
            if total and done >= total:
                workflow.status = 'COMPLETED'
                workflow.save()
        elif workflow and coord_status == 'PENDING' and workflow.status == 'RUNNING':
            # Reste RUNNING s'il reste des tâches assignées, sinon PENDING
            still_assigned = Task.objects(workflow=workflow, status__in=['ASSIGNED', 'RUNNING']).count()
            if still_assigned == 0:
                workflow.status = 'PENDING'
                workflow.save()

        _notify_frontend('task_status_changed', {
            'task_id': str(task.id),
            'task_name': task.name,
            'status': task.status,
            'new_status': task.status,
            'progress': task.progress,
            'workflow_id': str(workflow.id) if workflow else None,
        })
        logger.info("task/status_sync: %s -> %s", task_id, coord_status)
        if coord_status == 'PENDING':
            _trigger_coordinator_assignment()
        _sync_workflow_status(task.workflow)
    except Exception as e:
        logger.error("Erreur task/status_sync: %s", e)
        logger.error(traceback.format_exc())


def handle_workflow_tasks_ready(channel: str, message: Message):
    """Le Manager a fini de publier les tâches — lancer l'assignation."""
    try:
        data = message.data or {}
        workflow_id = data.get('workflow_id')
        logger.info(
            "workflow/tasks_ready: workflow %s (%s tâches)",
            workflow_id,
            data.get('task_count'),
        )
        _trigger_coordinator_assignment()
    except Exception as exc:
        logger.error("Erreur workflow/tasks_ready: %s", exc)


def handle_assign_request(channel: str, message: Message):
    """Demande explicite d'assignation (recovery manager, retry, etc.)."""
    logger.info("coordinator/assign_request reçu")
    _trigger_coordinator_assignment()


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
    client.subscribe('task/status_sync', handle_task_status_sync)
    client.subscribe('workflow/tasks_ready', handle_workflow_tasks_ready)
    client.subscribe('coordinator/assign_request', handle_assign_request)

    logger.info("Gestionnaires de statut des tâches enregistrés (incluant task/status)")