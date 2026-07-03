from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import MessageLog
from .serializers import MessageLogSerializer

class MessageLogViewSet(viewsets.ViewSet):
    """
    ViewSet pour visualiser les logs de messages.
    """
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        # Limiter aux 100 derniers messages pour éviter de surcharger
        queryset = MessageLog.objects.all().order_by('-timestamp')[:100]
        serializer = MessageLogSerializer(queryset, many=True)
        return Response(serializer.data)
