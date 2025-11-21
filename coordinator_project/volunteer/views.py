from rest_framework import viewsets, status,permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .utils.jwt_utils import generate_jwt
from .decorators.auth_decorators import jwt_required
from django.utils import timezone
from .models import Volunteer
from .serializers import VolunteerSerializer
from redis_communication.client import RedisClient
import logging

logger = logging.getLogger(__name__)

class VolunteerViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        volunteers = Volunteer.objects.all()
        serializer = VolunteerSerializer(volunteers, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = VolunteerSerializer(data=request.data)
        if serializer.is_valid():
            volunteer = serializer.save()
            return Response(VolunteerSerializer(volunteer).data, status=201)
        return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        try:
            volunteer = Volunteer.objects.get(id=pk)
        except Volunteer.DoesNotExist:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = VolunteerSerializer(volunteer)
        return Response(serializer.data)

    def update(self, request, pk=None):
        try:
            volunteer = Volunteer.objects.get(id=pk)
        except Volunteer.DoesNotExist:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = VolunteerSerializer(volunteer, data=request.data, partial=True)
        if serializer.is_valid():
            volunteer = serializer.save()
            return Response(VolunteerSerializer(volunteer).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            volunteer = Volunteer.objects.get(id=pk)
        except Volunteer.DoesNotExist:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)
        volunteer.delete()
        return Response({'success': 'Volunteer deleted'}, status=status.HTTP_204_NO_CONTENT)


    @action(detail=False, methods=['get'])
    @jwt_required
    def available(self, request):
        available_volunteers = Volunteer.objects(status='available')
        serializer = VolunteerDetailSerializer(available_volunteers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_tech_specs(self, request, pk=None):
        try:
            volunteer = Volunteer.objects.get(id=pk)
        except Volunteer.DoesNotExist:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)
        for field in ['cpu_model', 'cpu_cores', 'total_ram', 'available_storage', 'operating_system', 'gpu_available', 'gpu_model', 'gpu_memory']:
            if field in request.data:
                setattr(volunteer, field, request.data[field])
        volunteer.save()
        return Response(VolunteerDetailSerializer(volunteer).data)

    @action(detail=True, methods=['post'])
    def update_preferences(self, request, pk=None):
        try:
            volunteer = Volunteer.objects.get(id=pk)
        except Volunteer.DoesNotExist:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)
        new_preferences = request.data.get('preferences', {})
        volunteer.preferences.update(new_preferences)
        volunteer.save()
        return Response(VolunteerDetailSerializer(volunteer).data)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        try:
            volunteer = Volunteer.objects.get(id=pk)
        except Volunteer.DoesNotExist:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)
        new_status = request.data.get('status')
        if new_status not in ['offline', 'available', 'busy']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        volunteer.update_status(new_status)
        return Response({'status': 'updated'})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Active un volunteer (permet l'utilisation du système)"""
        try:
            volunteer = Volunteer.objects.get(id=pk)
            volunteer.is_active = True
            volunteer.save()

            # Publier sur Redis
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('volunteer/status', {
                    'id': str(volunteer.id),
                    'username': volunteer.username,
                    'name': volunteer.name,
                    'is_active': True,
                    'action': 'activated'
                })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response({
                'message': f'Volunteer {volunteer.name} activé avec succès',
                'is_active': volunteer.is_active
            })
        except Volunteer.DoesNotExist:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Désactive un volunteer (empêche l'utilisation du système)"""
        try:
            volunteer = Volunteer.objects.get(id=pk)
            reason = request.data.get('reason', 'Aucune raison fournie')
            volunteer.is_active = False
            volunteer.save()

            # Publier sur Redis
            try:
                redis_client = RedisClient.get_instance()
                redis_client.publish('volunteer/status', {
                    'id': str(volunteer.id),
                    'username': volunteer.username,
                    'name': volunteer.name,
                    'is_active': False,
                    'action': 'deactivated',
                    'reason': reason
                })
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur Redis: {e}")

            return Response({
                'message': f'Volunteer {volunteer.name} désactivé avec succès',
                'is_active': volunteer.is_active,
                'reason': reason
            })
        except Volunteer.DoesNotExist:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)
