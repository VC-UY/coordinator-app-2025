from rest_framework import serializers
from .models import Manager, Workflow, Task
from django.contrib.auth.hashers import make_password
from manager.models import Manager
from volunteer.models import Volunteer

# Serializer DRF classique pour MongoEngine (pas ModelSerializer)
class ManagerSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField()
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    registration_date = serializers.DateTimeField(required=False)
    last_login = serializers.DateTimeField(required=False)
    status = serializers.CharField()

    # Pour création d'un manager
    def create(self, validated_data):
        return Manager(**validated_data).save()

    # Pour mise à jour d'un manager
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        try:
            instance.save()
        except Exception as e:
            print(f'[ManagerSerializer.update] Erreur MongoEngine lors du save: {e}')
            raise serializers.ValidationError({'mongoengine': str(e)})
        return instance

class ManagerRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        manager = Manager(**validated_data)
        manager.save()
        return manager
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class ManagerDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField()
    email = serializers.EmailField()
    status = serializers.CharField()
    last_login = serializers.DateTimeField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

# Serializer DRF pour le modèle Workflow (MongoEngine)
class WorkflowSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    workflow_type = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    submitted_at = serializers.DateTimeField(allow_null=True, required=False)
    completed_at = serializers.DateTimeField(allow_null=True, required=False)
    priority = serializers.IntegerField(required=False)
    estimated_resources = serializers.DictField(required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    metadata = serializers.DictField(required=False)
    # owner = serializers.PrimaryKeyRelatedField(queryset=Manager.objects.all())
    owner = serializers.CharField()  # Utilise l'id du manager (UUID)

    def create(self, validated_data):
        owner_id = validated_data.pop('owner')
        owner = Manager.objects.get(id=owner_id)
        workflow = Workflow(owner=owner, **validated_data)
        workflow.save()
        return workflow

    def update(self, instance, validated_data):
        owner_id = validated_data.get('owner')
        if owner_id:
            instance.owner = Manager.objects.get(id=owner_id)
        for attr, value in validated_data.items():
            if attr != 'owner':
                setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        owner = getattr(instance, 'owner', None)
        return {
            'id': str(instance.id),
            'name': instance.name,
            'description': getattr(instance, 'description', '') or '',
            'workflow_type': instance.workflow_type,
            'status': instance.status,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
            'submitted_at': getattr(instance, 'submitted_at', None),
            'completed_at': getattr(instance, 'completed_at', None),
            'priority': getattr(instance, 'priority', 0),
            'estimated_resources': getattr(instance, 'estimated_resources', {}) or {},
            'tags': getattr(instance, 'tags', []) or [],
            'metadata': getattr(instance, 'metadata', {}) or {},
            'owner': str(owner.id) if owner else None,
            'owner_username': owner.username if owner else None,
            'owner_email': owner.email if owner else None,
        }
class TaskSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    workflow = serializers.CharField()  # UUID du workflow
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    command = serializers.CharField(allow_blank=True, required=False)
    dependencies = serializers.ListField(child=serializers.CharField(), required=False)
    status = serializers.CharField()
    is_subtask = serializers.BooleanField(required=False)
    progress = serializers.FloatField(required=False)
    created_at = serializers.DateTimeField(read_only=True)
    start_time = serializers.DateTimeField(allow_null=True, required=False)
    end_time = serializers.DateTimeField(allow_null=True, required=False)
    required_resources = serializers.DictField(required=False)
    assigned_to = serializers.CharField(allow_null=True, required=False)  # UUID du volontaire
    attempts = serializers.IntegerField(required=False)
    results = serializers.DictField(required=False, allow_null=True)
    error_details = serializers.DictField(required=False, allow_null=True)
    docker_image = serializers.CharField(allow_blank=True, allow_null=True, required=False)

    def create(self, validated_data):
        workflow_id = validated_data.pop('workflow')
        workflow = Workflow.objects.get(id=workflow_id)
        assigned_to_id = validated_data.pop('assigned_to', None)
        assigned_to = None
        if assigned_to_id:
            assigned_to = Volunteer.objects.get(id=assigned_to_id)
        task = Task(workflow=workflow, assigned_to=assigned_to, **validated_data)
        task.save()
        return task

    def update(self, instance, validated_data):
        workflow_id = validated_data.get('workflow')
        if workflow_id:
            instance.workflow = Workflow.objects.get(id=workflow_id)
        assigned_to_id = validated_data.get('assigned_to')
        if assigned_to_id is not None:
            instance.assigned_to = Volunteer.objects.get(id=assigned_to_id) if assigned_to_id else None
        for attr, value in validated_data.items():
            if attr not in ('workflow', 'assigned_to'):
                setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        workflow = getattr(instance, 'workflow', None)
        volunteer = getattr(instance, 'assigned_to', None)
        owner = getattr(workflow, 'owner', None) if workflow else None
        return {
            'id': str(instance.id),
            'workflow': str(workflow.id) if workflow else None,
            'workflow_name': workflow.name if workflow else None,
            'owner': str(owner.id) if owner else None,
            'owner_username': owner.username if owner else None,
            'owner_email': owner.email if owner else None,
            'name': instance.name,
            'description': getattr(instance, 'description', '') or '',
            'command': getattr(instance, 'command', '') or '',
            'dependencies': getattr(instance, 'dependencies', []) or [],
            'status': instance.status,
            'is_subtask': getattr(instance, 'is_subtask', False),
            'progress': getattr(instance, 'progress', 0) or 0,
            'created_at': instance.created_at,
            'start_time': getattr(instance, 'start_time', None),
            'end_time': getattr(instance, 'end_time', None),
            'required_resources': getattr(instance, 'required_resources', {}) or {},
            'assigned_to': str(volunteer.id) if volunteer else None,
            'assigned_to_name': volunteer.username if volunteer else None,
            'attempts': getattr(instance, 'attempts', 0),
            'results': getattr(instance, 'results', None),
            'error_details': getattr(instance, 'error_details', None),
            'docker_image': getattr(instance, 'docker_image', None),
        }
