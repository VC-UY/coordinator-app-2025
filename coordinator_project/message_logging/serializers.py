from rest_framework import serializers
from .models import MessageLog

class MessageLogSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    sender_type = serializers.CharField(required=False)
    sender_id = serializers.CharField(required=False)
    receiver_type = serializers.CharField(required=False, allow_null=True)
    receiver_id = serializers.CharField(required=False, allow_null=True)
    channel = serializers.CharField(required=False)
    request_id = serializers.CharField(required=False)
    message_type = serializers.CharField(required=False)
    content = serializers.CharField(required=False)
    timestamp = serializers.DateTimeField(read_only=True)
    is_processed = serializers.BooleanField(read_only=True)

    def to_representation(self, instance):
        """Convertit l'objet MongoEngine en dictionnaire."""
        data = super().to_representation(instance)
        # S'assurer que l'ID est une chaîne
        if hasattr(instance, 'id'):
            data['id'] = str(instance.id)
        return data
