from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from datetime import datetime, timezone, timedelta
import re
import logging

from .models import (
    LoginAttempt, RegistrationValidation, SecurityAlert,
    IPBlacklist, RateLimitTracker,
    LOGIN_SUCCESS, LOGIN_FAILED, LOGIN_BLOCKED,
    VALIDATION_PENDING, VALIDATION_APPROVED, VALIDATION_REJECTED,
    ALERT_SEVERITY_HIGH, ALERT_SEVERITY_CRITICAL
)
from .serializers import (
    LoginAttemptSerializer, RegistrationValidationSerializer,
    SecurityAlertSerializer, IPBlacklistSerializer,
    RateLimitTrackerSerializer
)
from manager.models import Manager
from volunteer.models import Volunteer

logger = logging.getLogger(__name__)


class LoginAttemptViewSet(viewsets.ViewSet):
    """ViewSet pour gérer les tentatives de connexion"""
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        """Liste toutes les tentatives de connexion"""
        attempts = LoginAttempt.objects.all()
        serializer = LoginAttemptSerializer(attempts, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Enregistre une nouvelle tentative de connexion"""
        serializer = LoginAttemptSerializer(data=request.data)
        if serializer.is_valid():
            attempt = serializer.save()

            # Vérifier si c'est suspect et créer une alerte si nécessaire
            if serializer.validated_data.get('status') == LOGIN_FAILED:
                self._check_for_suspicious_activity(
                    attempt.ip_address,
                    attempt.username,
                    attempt.client_type
                )

            return Response(LoginAttemptSerializer(attempt).data, status=201)
        return Response(serializer.errors, status=400)

    def _check_for_suspicious_activity(self, ip_address, username, client_type):
        """Vérifie s'il y a une activité suspecte"""
        # Compter les échecs récents (dernière heure)
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_failures = LoginAttempt.objects.filter(
            ip_address=ip_address,
            status=LOGIN_FAILED,
            timestamp__gte=one_hour_ago
        ).count()

        # Si plus de 5 échecs en 1 heure, créer une alerte et bloquer l'IP
        if recent_failures >= 5:
            # Créer une alerte de sécurité
            SecurityAlert(
                alert_type='brute_force',
                severity=ALERT_SEVERITY_HIGH,
                title=f'Tentative de force brute détectée',
                description=f'{recent_failures} tentatives de connexion échouées depuis {ip_address}',
                ip_address=ip_address,
                username=username,
                related_attempts_count=recent_failures,
                alert_details={'client_type': client_type},
                auto_blocked=True
            ).save()

            # Bloquer l'IP temporairement (24h)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            IPBlacklist(
                ip_address=ip_address,
                reason=f'Tentative de force brute détectée ({recent_failures} échecs)',
                blocked_by='auto',
                is_permanent=False,
                expires_at=expires_at,
                failed_attempts_count=recent_failures
            ).save()

            logger.warning(f"IP {ip_address} bloquée automatiquement après {recent_failures} échecs")


class RegistrationValidationViewSet(viewsets.ViewSet):
    """ViewSet pour gérer les validations d'enregistrement"""
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        """Liste toutes les validations d'enregistrement"""
        validations = RegistrationValidation.objects.all()
        serializer = RegistrationValidationSerializer(validations, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Crée une nouvelle validation d'enregistrement"""
        serializer = RegistrationValidationSerializer(data=request.data)
        if serializer.is_valid():
            # Effectuer des validations automatiques
            validated_data = serializer.validated_data
            validation_result = self._perform_validation_checks(validated_data)

            # Mettre à jour les données avec les résultats de validation
            validated_data.update(validation_result)

            validation = serializer.save()
            return Response(RegistrationValidationSerializer(validation).data, status=201)
        return Response(serializer.errors, status=400)

    def _perform_validation_checks(self, data):
        """Effectue les vérifications de validation"""
        result = {
            'email_valid': self._validate_email(data.get('email')),
            'password_strength_score': 3,  # Placeholder
            'ip_reputation_score': 70,  # Placeholder
            'duplicate_check_passed': self._check_duplicates(data.get('username'), data.get('email')),
            'validation_status': VALIDATION_PENDING,
            'validation_details': {}
        }

        # Décision automatique si tous les checks passent
        if (result['email_valid'] and
            result['duplicate_check_passed'] and
            result['ip_reputation_score'] >= 50):
            result['validation_status'] = VALIDATION_APPROVED
        elif not result['duplicate_check_passed']:
            result['validation_status'] = VALIDATION_REJECTED
            result['rejection_reason'] = 'Compte en double détecté'

        return result

    def _validate_email(self, email):
        """Valide le format de l'email"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, email))

    def _check_duplicates(self, username, email):
        """Vérifie les doublons dans managers et volunteers"""
        # Vérifier dans les managers
        manager_exists = Manager.objects.filter(username=username).count() > 0
        manager_email_exists = Manager.objects.filter(email=email).count() > 0

        # Vérifier dans les volunteers
        volunteer_exists = Volunteer.objects.filter(username=username).count() > 0

        return not (manager_exists or manager_email_exists or volunteer_exists)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approuve une validation"""
        try:
            validation = RegistrationValidation.objects.get(id=pk)
            validation.validation_status = VALIDATION_APPROVED
            validation.validated_at = datetime.now(timezone.utc)
            validation.validated_by = request.user.username if request.user.is_authenticated else 'system'
            validation.save()

            return Response({
                'success': True,
                'message': 'Validation approuvée',
                'validation': RegistrationValidationSerializer(validation).data
            })
        except RegistrationValidation.DoesNotExist:
            return Response({'error': 'Validation non trouvée'}, status=404)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rejette une validation"""
        try:
            validation = RegistrationValidation.objects.get(id=pk)
            validation.validation_status = VALIDATION_REJECTED
            validation.validated_at = datetime.now(timezone.utc)
            validation.validated_by = request.user.username if request.user.is_authenticated else 'system'
            validation.rejection_reason = request.data.get('reason', 'Rejeté par l\'administrateur')
            validation.save()

            return Response({
                'success': True,
                'message': 'Validation rejetée',
                'validation': RegistrationValidationSerializer(validation).data
            })
        except RegistrationValidation.DoesNotExist:
            return Response({'error': 'Validation non trouvée'}, status=404)


class SecurityAlertViewSet(viewsets.ViewSet):
    """ViewSet pour gérer les alertes de sécurité"""
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        """Liste toutes les alertes de sécurité"""
        alerts = SecurityAlert.objects.all()
        serializer = SecurityAlertSerializer(alerts, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Crée une nouvelle alerte de sécurité"""
        serializer = SecurityAlertSerializer(data=request.data)
        if serializer.is_valid():
            alert = serializer.save()
            return Response(SecurityAlertSerializer(alert).data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Résout une alerte de sécurité"""
        try:
            alert = SecurityAlert.objects.get(id=pk)
            alert.is_resolved = True
            alert.resolved_at = datetime.now(timezone.utc)
            alert.resolved_by = request.user.username if request.user.is_authenticated else 'system'
            alert.resolution_notes = request.data.get('notes', '')
            alert.save()

            return Response({
                'success': True,
                'message': 'Alerte résolue',
                'alert': SecurityAlertSerializer(alert).data
            })
        except SecurityAlert.DoesNotExist:
            return Response({'error': 'Alerte non trouvée'}, status=404)


class IPBlacklistViewSet(viewsets.ViewSet):
    """ViewSet pour gérer la liste noire des IPs"""
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        """Liste toutes les IPs bloquées"""
        blacklist = IPBlacklist.objects.all()
        serializer = IPBlacklistSerializer(blacklist, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Ajoute une IP à la liste noire"""
        serializer = IPBlacklistSerializer(data=request.data)
        if serializer.is_valid():
            blacklist_entry = serializer.save()
            return Response(IPBlacklistSerializer(blacklist_entry).data, status=201)
        return Response(serializer.errors, status=400)

    def destroy(self, request, pk=None):
        """Supprime une IP de la liste noire"""
        try:
            entry = IPBlacklist.objects.get(id=pk)
            entry.delete()
            return Response({'success': 'IP supprimée de la liste noire'}, status=204)
        except IPBlacklist.DoesNotExist:
            return Response({'error': 'Entrée non trouvée'}, status=404)

    @action(detail=False, methods=['post'])
    def check(self, request):
        """Vérifie si une IP est bloquée"""
        ip_address = request.data.get('ip_address')
        if not ip_address:
            return Response({'error': 'IP manquante'}, status=400)

        # Vérifier si l'IP est dans la liste noire et active
        now = datetime.now(timezone.utc)
        blocked = IPBlacklist.objects.filter(
            ip_address=ip_address,
            is_active=True
        ).first()

        if blocked:
            # Vérifier si le blocage est expiré
            if not blocked.is_permanent and blocked.expires_at and blocked.expires_at < now:
                blocked.is_active = False
                blocked.save()
                return Response({'blocked': False, 'reason': 'Blocage expiré'})

            return Response({
                'blocked': True,
                'reason': blocked.reason,
                'is_permanent': blocked.is_permanent,
                'expires_at': blocked.expires_at
            })

        return Response({'blocked': False})


class ValidationStatsView(APIView):
    """Vue pour les statistiques de validation"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Retourne les statistiques de validation"""
        # Compteurs de base
        total_attempts = LoginAttempt.objects.count()
        failed_attempts = LoginAttempt.objects.filter(status=LOGIN_FAILED).count()
        success_attempts = LoginAttempt.objects.filter(status=LOGIN_SUCCESS).count()

        total_registrations = RegistrationValidation.objects.count()
        pending_registrations = RegistrationValidation.objects.filter(
            validation_status=VALIDATION_PENDING
        ).count()
        approved_registrations = RegistrationValidation.objects.filter(
            validation_status=VALIDATION_APPROVED
        ).count()
        rejected_registrations = RegistrationValidation.objects.filter(
            validation_status=VALIDATION_REJECTED
        ).count()

        total_alerts = SecurityAlert.objects.count()
        unresolved_alerts = SecurityAlert.objects.filter(is_resolved=False).count()
        critical_alerts = SecurityAlert.objects.filter(
            severity=ALERT_SEVERITY_CRITICAL,
            is_resolved=False
        ).count()

        total_blocked_ips = IPBlacklist.objects.filter(is_active=True).count()

        return Response({
            'login_attempts': {
                'total': total_attempts,
                'success': success_attempts,
                'failed': failed_attempts,
                'success_rate': round((success_attempts / total_attempts * 100) if total_attempts > 0 else 0, 2)
            },
            'registrations': {
                'total': total_registrations,
                'pending': pending_registrations,
                'approved': approved_registrations,
                'rejected': rejected_registrations
            },
            'security_alerts': {
                'total': total_alerts,
                'unresolved': unresolved_alerts,
                'critical': critical_alerts
            },
            'blocked_ips': total_blocked_ips
        })
