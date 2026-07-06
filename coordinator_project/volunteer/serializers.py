from rest_framework import serializers
from .models import Volunteer


def _machine_display_id(volunteer) -> str:
    """Identifiant machine basé sur MAC (jamais l'IP publique)."""
    info = getattr(volunteer, 'machine_info', None) or {}
    mac = info.get('adresse_mac') if isinstance(info, dict) else None
    if mac:
        mac_str = str(mac)
        if len(mac_str) > 8:
            return f"mac:{mac_str[:8]}…"
        return f"mac:{mac_str}"
    return getattr(volunteer, 'name', '') or str(getattr(volunteer, 'id', ''))

class VolunteerSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    username = serializers.CharField(required=False)
    cpu_model = serializers.CharField(required=False)
    cpu_cores = serializers.IntegerField(required=False)
    total_ram = serializers.IntegerField(required=False)
    available_storage = serializers.IntegerField(required=False)
    operating_system = serializers.CharField(required=False)
    last_update = serializers.DateTimeField(required=False)
    current_status = serializers.CharField()
    gpu_available = serializers.BooleanField(required=False)
    gpu_model = serializers.CharField(allow_null=True, required=False)
    gpu_memory = serializers.IntegerField(allow_null=True, required=False)
    ip_address = serializers.CharField(required=False)
    communication_port = serializers.IntegerField(required=False)
    preferences = serializers.DictField(required=False)
    performance = serializers.DictField(required=False)
    last_activity = serializers.DateTimeField(allow_null=True, required=False)
    is_active = serializers.BooleanField(default=True, required=False)

    def create(self, validated_data):
        volunteer = Volunteer(**validated_data)
        volunteer.save()
        return volunteer

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        from volunteer.presence import is_online

        online = is_online(instance)
        # Afficher offline si pas de heartbeat récent, même si le champ DB est périmé
        status = instance.current_status if online else 'offline'
        return {
            'id': str(instance.id),
            'name': instance.name,
            'username': getattr(instance, 'username', None),
            'current_status': status,
            'is_online': online,
            'cpu_model': getattr(instance, 'cpu_model', None),
            'cpu_cores': getattr(instance, 'cpu_cores', None),
            'total_ram': getattr(instance, 'total_ram', None),
            'available_storage': getattr(instance, 'available_storage', None),
            'operating_system': getattr(instance, 'operating_system', None),
            'last_update': getattr(instance, 'last_update', None),
            'gpu_available': getattr(instance, 'gpu_available', False),
            'gpu_model': getattr(instance, 'gpu_model', None),
            'gpu_memory': getattr(instance, 'gpu_memory', None),
            'machine_id': _machine_display_id(instance),
            'communication_port': getattr(instance, 'communication_port', None),
            'preferences': getattr(instance, 'preferences', {}) or {},
            'performance': getattr(instance, 'performance', {}) or {},
            'last_activity': getattr(instance, 'last_activity', None),
            'last_seen': getattr(instance, 'last_activity', None),
            'is_active': getattr(instance, 'is_active', True),
        }