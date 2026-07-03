from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework import status as drf_status
from mongoengine.connection import get_db
from datetime import datetime, timezone
from volunteer.models import Volunteer
from .models import Manager, Workflow, Task
from .serializers import (
    ManagerSerializer,
    ManagerRegistrationSerializer,
    ManagerDetailSerializer,
    WorkflowSerializer,
    TaskSerializer
)
from redis_communication.client import RedisClient
import logging

logger = logging.getLogger(__name__)

# ViewSet personnalisé pour MongoEngine
class ManagerViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    # Liste tous les managers
    def list(self, request):
        managers = Manager.objects.all()
        serializer = ManagerSerializer(managers, many=True)
        return Response(serializer.data)

    # Crée un nouveau manager
    def create(self, request):
        serializer = ManagerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Enregistrer dans MongoDB
            manager = serializer.save()

            # Publier sur Redis pour informer les volunteers
            message_data = {
                'username': manager.username,
                'email': manager.email,
                'status': manager.status,
                'id': str(manager.id)
            }

            # Publier sur le canal d'enregistrement via RedisClient
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('auth/register', message_data)
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response(ManagerDetailSerializer(manager).data, status=201)
        return Response(serializer.errors, status=400)

    # Met à jour un manager existant
    def update(self, request, pk=None):
        try:
            manager = Manager.objects.get(id=pk)
        except Manager.DoesNotExist:
            return Response({'error': 'Manager not found'}, status=status.HTTP_404_NOT_FOUND)
        # Utilise ManagerSerializer pour la mise à jour (inclut status)
        serializer = ManagerSerializer(manager, data=request.data, partial=True)
        if serializer.is_valid():
            manager = serializer.save()

            # Si le statut a changé, publier sur Redis
            if 'status' in request.data:
                try:
                    redis_client = RedisClient.get_instance()
                    redis_client.publish('manager/status', {
                        'id': str(manager.id),
                        'username': manager.username,
                        'status': manager.status
                    })
                except Exception as e:
                    logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response(ManagerSerializer(manager).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Met à jour partielle (PATCH)
    def partial_update(self, request, pk=None):
        return self.update(request, pk)

    # Récupère le détail d'un manager (GET /manager/{id}/)
    def retrieve(self, request, pk=None):
        try:
            manager = Manager.objects.get(id=pk)
        except Manager.DoesNotExist:
            return Response({'error': 'Manager not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ManagerDetailSerializer(manager)
        return Response(serializer.data)

    # Supprime un manager (DELETE /manager/{id}/)
    def destroy(self, request, pk=None):
        try:
            manager = Manager.objects.get(id=pk)

            # Publier la déconnexion sur Redis
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('manager/disconnect', {
                    'id': str(manager.id),
                    'username': manager.username
                })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            # Supprimer de MongoDB
            manager.delete()

            return Response({'success': 'Manager deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Manager.DoesNotExist:
            return Response({'error': 'Manager not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Active un manager (change le statut à 'active')"""
        try:
            manager = Manager.objects.get(id=pk)
            old_status = manager.status
            manager.status = 'active'
            manager.save()

            # Publier sur Redis
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('manager/status', {
                    'id': str(manager.id),
                    'username': manager.username,
                    'old_status': old_status,
                    'new_status': manager.status,
                    'action': 'activated'
                })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response({
                'message': f'Manager {manager.username} activé avec succès',
                'status': manager.status
            })
        except Manager.DoesNotExist:
            return Response({'error': 'Manager not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Désactive un manager (change le statut à 'inactive')"""
        try:
            manager = Manager.objects.get(id=pk)
            old_status = manager.status
            manager.status = 'inactive'
            manager.save()

            # Publier sur Redis
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('manager/status', {
                    'id': str(manager.id),
                    'username': manager.username,
                    'old_status': old_status,
                    'new_status': manager.status,
                    'action': 'deactivated'
                })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response({
                'message': f'Manager {manager.username} désactivé avec succès',
                'status': manager.status
            })
        except Manager.DoesNotExist:
            return Response({'error': 'Manager not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend un manager (change le statut à 'suspended')"""
        try:
            manager = Manager.objects.get(id=pk)
            reason = request.data.get('reason', 'Aucune raison fournie')
            old_status = manager.status
            manager.status = 'suspended'
            manager.save()

            # Publier sur Redis
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('manager/status', {
                    'id': str(manager.id),
                    'username': manager.username,
                    'old_status': old_status,
                    'new_status': manager.status,
                    'action': 'suspended',
                    'reason': reason
                })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response({
                'message': f'Manager {manager.username} suspendu avec succès',
                'status': manager.status,
                'reason': reason
            })
        except Manager.DoesNotExist:
            return Response({'error': 'Manager not found'}, status=status.HTTP_404_NOT_FOUND)


# ViewSet pour le modèle Workflow (MongoEngine)
class WorkflowViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    # Liste tous les workflows
    def list(self, request):
        workflows = Workflow.objects.all()
        owner_id = request.query_params.get('owner')
        manager_email = request.query_params.get('manager_email')
        status_filter = request.query_params.get('status')

        if owner_id:
            try:
                manager = Manager.objects.get(id=owner_id)
                workflows = workflows.filter(owner=manager)
            except Manager.DoesNotExist:
                workflows = Workflow.objects.none()
        if manager_email:
            managers = list(Manager.objects.filter(email=manager_email))
            workflows = workflows.filter(owner__in=managers) if managers else Workflow.objects.none()
        if status_filter:
            workflows = workflows.filter(status=status_filter)

        serializer = WorkflowSerializer(workflows, many=True)
        return Response(serializer.data)

    # Crée un nouveau workflow
    def create(self, request):
        serializer = WorkflowSerializer(data=request.data)
        if serializer.is_valid():
            workflow = serializer.save()

            # Publier sur Redis pour informer les volunteers
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('workflow/created', {
                    'workflow_id': str(workflow.id),
                    'name': workflow.name,
                    'type': workflow.workflow_type,
                    'owner': str(workflow.owner.id),
                    'priority': workflow.priority,
                    'status': workflow.status
                })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response(WorkflowSerializer(workflow).data, status=201)
        return Response(serializer.errors, status=400)

    # Détail d'un workflow
    def retrieve(self, request, pk=None):
        try:
            workflow = Workflow.objects.get(id=pk)
        except Workflow.DoesNotExist:
            return Response({'error': 'Workflow not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = WorkflowSerializer(workflow)
        return Response(serializer.data)

    # Mise à jour d'un workflow
    def update(self, request, pk=None):
        try:
            workflow = Workflow.objects.get(id=pk)
        except Workflow.DoesNotExist:
            return Response({'error': 'Workflow not found'}, status=status.HTTP_404_NOT_FOUND)

        # Sauvegarder l'ancien statut pour détecter les changements
        old_status = workflow.status

        serializer = WorkflowSerializer(workflow, data=request.data, partial=True)
        if serializer.is_valid():
            workflow = serializer.save()
            workflow.updated_at = datetime.now(timezone.utc)
            workflow.save()

            # Si le statut a changé, publier sur Redis
            if 'status' in request.data and old_status != workflow.status:
                try:
                    redis_client = RedisClient.get_instance()
                    redis_client.publish('workflow/status_changed', {
                        'workflow_id': str(workflow.id),
                        'name': workflow.name,
                        'old_status': old_status,
                        'new_status': workflow.status
                    })
                except Exception as e:
                    logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response(WorkflowSerializer(workflow).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Mise à jour partielle d'un workflow
    def partial_update(self, request, pk=None):
        return self.update(request, pk)

    # Suppression d'un workflow
    def destroy(self, request, pk=None):
        try:
            workflow = Workflow.objects.get(id=pk)

            # Publier la suppression sur Redis
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('workflow/deleted', {
                    'workflow_id': str(workflow.id),
                    'name': workflow.name
                })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            workflow.delete()
            return Response({'success': 'Workflow deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Workflow.DoesNotExist:
            return Response({'error': 'Workflow not found'}, status=status.HTTP_404_NOT_FOUND)

    # Action personnalisée pour arrêter un workflow
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """
        Arrête l'exécution d'un workflow en cours
        """
        try:
            workflow = Workflow.objects.get(id=pk)

            # Vérifier que le workflow est dans un état stoppable
            stoppable_statuses = ['RUNNING', 'PENDING', 'ASSIGNING', 'SPLITTING']
            if workflow.status not in stoppable_statuses:
                return Response({
                    'error': f'Cannot stop workflow in status {workflow.status}',
                    'message': f'Only workflows with status {", ".join(stoppable_statuses)} can be stopped'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Sauvegarder l'ancien statut
            old_status = workflow.status

            # Mettre à jour le statut
            workflow.status = 'PAUSED'
            workflow.updated_at = datetime.now(timezone.utc)
            workflow.save()

            # Publier sur Redis pour notifier les volontaires
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('workflow/stopped', {
                    'workflow_id': str(workflow.id),
                    'name': workflow.name,
                    'old_status': old_status,
                    'new_status': 'PAUSED'
                })

                # Arrêter toutes les tâches en cours de ce workflow
                tasks = Task.objects.filter(workflow=workflow, status__in=['RUNNING', 'ASSIGNED'])
                for task in tasks:
                    task.status = 'PAUSED'
                    task.save()
                    redis_client.publish('task/stopped', {
                        'task_id': str(task.id),
                        'workflow_id': str(workflow.id)
                    })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response({
                'success': True,
                'message': f'Workflow {workflow.name} stopped successfully',
                'workflow': WorkflowSerializer(workflow).data
            })

        except Workflow.DoesNotExist:
            return Response({'error': 'Workflow not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du workflow: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Action personnalisée pour reprendre un workflow
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """
        Reprend l'exécution d'un workflow en pause
        """
        try:
            workflow = Workflow.objects.get(id=pk)

            # Vérifier que le workflow est en pause
            if workflow.status != 'PAUSED':
                return Response({
                    'error': f'Cannot resume workflow in status {workflow.status}',
                    'message': 'Only workflows with status PAUSED can be resumed'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Mettre à jour le statut
            workflow.status = 'RUNNING'
            workflow.updated_at = datetime.now(timezone.utc)
            workflow.save()

            # Publier sur Redis pour notifier les volontaires
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('workflow/resumed', {
                    'workflow_id': str(workflow.id),
                    'name': workflow.name,
                    'status': 'RUNNING'
                })

                # Reprendre toutes les tâches en pause de ce workflow
                tasks = Task.objects.filter(workflow=workflow, status='PAUSED')
                for task in tasks:
                    # Si la tâche était en cours d'exécution, la remettre en RUNNING
                    # Sinon la remettre en ASSIGNED
                    if task.start_time:
                        task.status = 'RUNNING'
                    else:
                        task.status = 'ASSIGNED'
                    task.save()
                    redis_client.publish('task/resumed', {
                        'task_id': str(task.id),
                        'workflow_id': str(workflow.id),
                        'status': task.status
                    })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response({
                'success': True,
                'message': f'Workflow {workflow.name} resumed successfully',
                'workflow': WorkflowSerializer(workflow).data
            })

        except Workflow.DoesNotExist:
            return Response({'error': 'Workflow not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur lors de la reprise du workflow: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ViewSet pour le modèle Task (MongoEngine)
class TaskViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    # Liste toutes les tâches
    def list(self, request):
        """Liste toutes les tâches avec possibilité de filtrer par workflow ou manager"""
        workflow_id = request.query_params.get('workflow', None)
        owner_id = request.query_params.get('owner')
        manager_email = request.query_params.get('manager_email')

        if workflow_id:
            try:
                workflow = Workflow.objects.get(id=workflow_id)
                tasks = Task.objects.filter(workflow=workflow)
            except Workflow.DoesNotExist:
                tasks = Task.objects.none()
        else:
            tasks = Task.objects.all()

        managers = []
        if owner_id:
            try:
                managers = [Manager.objects.get(id=owner_id)]
            except Manager.DoesNotExist:
                managers = []
        elif manager_email:
            managers = list(Manager.objects.filter(email=manager_email))

        if owner_id or manager_email:
            workflows = list(Workflow.objects.filter(owner__in=managers)) if managers else []
            tasks = tasks.filter(workflow__in=workflows) if workflows else Task.objects.none()

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    # Crée une nouvelle tâche
    def create(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save()

            # Publier sur Redis pour informer les volunteers
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('task/created', {
                    'task_id': str(task.id),
                    'name': task.name,
                    'workflow_id': str(task.workflow.id),
                    'required_resources': task.required_resources,
                    'status': task.status
                })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response(TaskSerializer(task).data, status=201)
        return Response(serializer.errors, status=400)

    # Détail d'une tâche
    def retrieve(self, request, pk=None):
        try:
            task = Task.objects.get(id=pk)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TaskSerializer(task)
        return Response(serializer.data)

    # Mise à jour d'une tâche
    def update(self, request, pk=None):
        try:
            task = Task.objects.get(id=pk)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            task = serializer.save()

            # Si le statut a changé, publier sur Redis
            if 'status' in request.data:
                try:
                    redis_client = RedisClient.get_instance()
                    redis_client.publish('task/status_changed', {
                        'task_id': str(task.id),
                        'name': task.name,
                        'status': task.status,
                        'progress': task.progress,
                        'workflow_id': str(task.workflow.id)
                    })
                except Exception as e:
                    logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response(TaskSerializer(task).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Mise à jour partielle d'une tâche
    def partial_update(self, request, pk=None):
        return self.update(request, pk)

    # Suppression d'une tâche
    def destroy(self, request, pk=None):
        try:
            task = Task.objects.get(id=pk)

            # Publier la suppression sur Redis
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('task/deleted', {
                    'task_id': str(task.id),
                    'name': task.name,
                    'workflow_id': str(task.workflow.id)
                })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            task.delete()
            return Response({'success': 'Task deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    # Action personnalisée pour arrêter une tâche
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """
        Arrête l'exécution d'une tâche en cours
        """
        try:
            task = Task.objects.get(id=pk)

            # Vérifier que la tâche est dans un état stoppable
            stoppable_statuses = ['RUNNING', 'ASSIGNED']
            if task.status not in stoppable_statuses:
                return Response({
                    'error': f'Cannot stop task in status {task.status}',
                    'message': f'Only tasks with status {", ".join(stoppable_statuses)} can be stopped'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Sauvegarder l'ancien statut
            old_status = task.status

            # Mettre à jour le statut
            task.status = 'PAUSED'
            task.save()

            # Publier sur Redis pour notifier les volontaires
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('task/stopped', {
                    'task_id': str(task.id),
                    'name': task.name,
                    'workflow_id': str(task.workflow.id),
                    'old_status': old_status,
                    'new_status': 'PAUSED',
                    'assigned_to': str(task.assigned_to.id) if task.assigned_to else None
                })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response({
                'success': True,
                'message': f'Task {task.name} stopped successfully',
                'task': TaskSerializer(task).data
            })

        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt de la tâche: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Action personnalisée pour reprendre une tâche
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """
        Reprend l'exécution d'une tâche en pause
        """
        try:
            task = Task.objects.get(id=pk)

            # Vérifier que la tâche est en pause
            if task.status != 'PAUSED':
                return Response({
                    'error': f'Cannot resume task in status {task.status}',
                    'message': 'Only tasks with status PAUSED can be resumed'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Déterminer le nouveau statut selon si la tâche avait démarré
            if task.start_time:
                task.status = 'RUNNING'
            else:
                task.status = 'ASSIGNED'
            task.save()

            # Publier sur Redis pour notifier les volontaires
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('task/resumed', {
                    'task_id': str(task.id),
                    'name': task.name,
                    'workflow_id': str(task.workflow.id),
                    'status': task.status,
                    'assigned_to': str(task.assigned_to.id) if task.assigned_to else None
                })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response({
                'success': True,
                'message': f'Task {task.name} resumed successfully',
                'task': TaskSerializer(task).data
            })

        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur lors de la reprise de la tâche: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Action personnalisée pour vérifier les dépendances
    @action(detail=True, methods=['get'])
    def dependencies(self, request, pk=None):
        """
        Retourne les dépendances d'une tâche et vérifie si elles sont satisfaites
        """
        try:
            task = Task.objects.get(id=pk)

            if not task.dependencies:
                return Response({
                    'has_dependencies': False,
                    'dependencies': [],
                    'all_satisfied': True
                })

            # Récupérer les informations sur chaque dépendance
            dependencies_info = []
            all_satisfied = True

            for dep_id in task.dependencies:
                try:
                    dep_task = Task.objects.get(id=dep_id)
                    is_satisfied = dep_task.status == 'COMPLETED'
                    all_satisfied = all_satisfied and is_satisfied

                    dependencies_info.append({
                        'id': str(dep_task.id),
                        'name': dep_task.name,
                        'status': dep_task.status,
                        'satisfied': is_satisfied
                    })
                except Task.DoesNotExist:
                    dependencies_info.append({
                        'id': dep_id,
                        'name': 'Unknown',
                        'status': 'NOT_FOUND',
                        'satisfied': False
                    })
                    all_satisfied = False

            return Response({
                'has_dependencies': True,
                'dependencies': dependencies_info,
                'all_satisfied': all_satisfied,
                'can_start': all_satisfied
            })

        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des dépendances: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# System Health check endpoint
class SystemHealthView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """
        Endpoint pour vérifier l'état du système
        """
        try:
            # Vérifier la connexion à MongoDB
            db = get_db()
            db_status = "connected" if db else "disconnected"
            
            # Compter les volunteers actifs
            active_volunteers = Volunteer.objects.filter(current_status='available').count()
            
            # Simuler d'autres vérifications de santé
            # Dans une application réelle, vous pourriez vérifier d'autres systèmes
            recent_errors = 0  # Ceci serait déterminé par un système de logging
            
            # Construire la réponse
            health_data = {
                "status": "ok" if db_status == "connected" else "warning",
                "details": {
                    "database": db_status,
                    "active_volunteers": active_volunteers,
                    "recent_errors": recent_errors,
                    "redis_connection": "connected"  # Vous pourriez vérifier cela dynamiquement
                }
            }
            
            return Response(health_data)
        except Exception as e:
            return Response({
                "status": "error",
                "details": {
                    "message": str(e)
                }
            }, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)


# Vue pour obtenir les données sur le statut des workflows
class WorkflowStatusView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """
        Endpoint pour obtenir la distribution des statuts des workflows
        """
        try:
            # Obtenir tous les workflows
            workflows = Workflow.objects.all()
            
            # Compter les workflows par statut
            status_counts = {}
            for workflow in workflows:
                status = workflow.status
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts[status] = 1
            
            result = [{"name": status, "value": count} for status, count in status_counts.items()]
            return Response(result)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)


# Vue pour obtenir les données sur le statut des volunteers
class VolunteerStatusView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """
        Endpoint pour obtenir la distribution des statuts des volunteers
        """
        try:
            # Obtenir tous les volunteers
            volunteers = Volunteer.objects.all()
            
            # Compter les volunteers par statut
            status_counts = {}
            for volunteer in volunteers:
                status = volunteer.current_status  # Utiliser current_status au lieu de status
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts[status] = 1
            
            result = [{"name": status, "value": count} for status, count in status_counts.items()]
            return Response(result)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)


# Vue pour obtenir les données de performance des tâches
class TaskPerformanceView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """
        Endpoint pour obtenir les données de performance des tâches
        """
        try:
            # Obtenir toutes les tâches
            tasks = Task.objects.all()
            
            # Calculer le temps moyen d'exécution par type de tâche
            # Dans un cas réel, vous auriez des données plus précises
            task_types = {}
            for task in tasks:
                task_type = task.name.split()[0] if task.name else "Unknown"
                
                # Simuler des données de performance
                if task_type not in task_types:
                    task_types[task_type] = {
                        "count": 0,
                        "total_time": 0,
                        "success_rate": 0
                    }
                
                task_types[task_type]["count"] += 1
                
                execution_time = 0
                if task.start_time and task.end_time:
                    execution_time = (task.end_time - task.start_time).total_seconds() / 60
                task_types[task_type]["total_time"] += execution_time

                if str(task.status).upper() in ("COMPLETED", "COMPLETE"):
                    task_types[task_type]["success_rate"] += 1
            
            result = []
            for task_type, data in task_types.items():
                count = data["count"]
                avg_time = data["total_time"] / count if count > 0 else 0
                success_rate = (data["success_rate"] / count * 100) if count > 0 else 0
                
                result.append({
                    "name": task_type,
                    "avgExecutionTime": round(avg_time, 2),
                    "successRate": round(success_rate, 2),
                    "count": count
                })
            return Response(result)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)


# Vue pour obtenir les données d'utilisation des ressources
class ResourceUtilizationView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Liste les volontaires avec leur statut reel (pas de metriques inventees)."""
        try:
            volunteers = Volunteer.objects.all()
            resource_data = []
            for volunteer in volunteers:
                resource_data.append({
                    "id": str(volunteer.id),
                    "name": volunteer.name or volunteer.username,
                    "username": volunteer.username,
                    "status": volunteer.current_status,
                })
            return Response(resource_data)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)


