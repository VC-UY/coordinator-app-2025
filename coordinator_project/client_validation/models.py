import uuid
from mongoengine import (
    Document, StringField, DateTimeField, UUIDField,
    BooleanField, IntField, DictField, ReferenceField
)
from datetime import datetime, timezone
from manager.models import Manager
from volunteer.models import Volunteer

# Status constants for login attempts
LOGIN_SUCCESS = 'success'
LOGIN_FAILED = 'failed'
LOGIN_BLOCKED = 'blocked'

LOGIN_ATTEMPT_STATUS_CHOICES = [
    (LOGIN_SUCCESS, 'Success'),
    (LOGIN_FAILED, 'Failed'),
    (LOGIN_BLOCKED, 'Blocked'),
]

# Alert severity levels
ALERT_SEVERITY_LOW = 'low'
ALERT_SEVERITY_MEDIUM = 'medium'
ALERT_SEVERITY_HIGH = 'high'
ALERT_SEVERITY_CRITICAL = 'critical'

ALERT_SEVERITY_CHOICES = [
    (ALERT_SEVERITY_LOW, 'Low'),
    (ALERT_SEVERITY_MEDIUM, 'Medium'),
    (ALERT_SEVERITY_HIGH, 'High'),
    (ALERT_SEVERITY_CRITICAL, 'Critical'),
]

# Validation status
VALIDATION_PENDING = 'pending'
VALIDATION_APPROVED = 'approved'
VALIDATION_REJECTED = 'rejected'

VALIDATION_STATUS_CHOICES = [
    (VALIDATION_PENDING, 'Pending'),
    (VALIDATION_APPROVED, 'Approved'),
    (VALIDATION_REJECTED, 'Rejected'),
]


class LoginAttempt(Document):
    """
    Modèle pour tracer toutes les tentatives de connexion (succès et échecs).
    Permet de détecter les tentatives frauduleuses et les attaques par force brute.
    """
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    username = StringField(max_length=255, required=True)
    email = StringField(max_length=255)
    ip_address = StringField(required=True)
    user_agent = StringField(max_length=500)
    status = StringField(max_length=20, choices=LOGIN_ATTEMPT_STATUS_CHOICES, required=True)
    timestamp = DateTimeField(default=datetime.now(timezone.utc))
    failure_reason = StringField(max_length=500)
    location_data = DictField(default=dict)  # Géolocalisation approximative
    is_suspicious = BooleanField(default=False)
    client_type = StringField(max_length=20, choices=[
        ('manager', 'Manager'),
        ('volunteer', 'Volunteer'),
    ], default='manager')

    # Référence optionnelle au manager ou volunteer si la connexion a réussi
    manager_ref = ReferenceField('Manager', null=True)
    volunteer_ref = ReferenceField('Volunteer', null=True)

    meta = {
        'collection': 'login_attempts',
        'ordering': ['-timestamp'],
        'indexes': [
            'username',
            'email',
            'ip_address',
            'status',
            'timestamp',
            'is_suspicious'
        ]
    }

    def __str__(self):
        return f"Login attempt by {self.username} from {self.ip_address} - {self.status}"


class RegistrationValidation(Document):
    """
    Modèle pour valider les nouvelles inscriptions de clients.
    Permet de vérifier la validité des données et détecter les inscriptions frauduleuses.
    """
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    username = StringField(max_length=255, required=True)
    email = StringField(max_length=255, required=True)
    ip_address = StringField(required=True)
    registration_date = DateTimeField(default=datetime.now(timezone.utc))
    validation_status = StringField(
        max_length=20,
        choices=VALIDATION_STATUS_CHOICES,
        default=VALIDATION_PENDING
    )
    client_type = StringField(max_length=20, choices=[
        ('manager', 'Manager'),
        ('volunteer', 'Volunteer'),
    ], required=True)

    # Référence au manager ou volunteer créé
    manager_ref = ReferenceField('Manager', null=True)
    volunteer_ref = ReferenceField('Volunteer', null=True)

    # Résultats des validations
    email_valid = BooleanField(default=False)
    password_strength_score = IntField(default=0)  # Score de 0 à 5
    ip_reputation_score = IntField(default=50)  # Score de 0 à 100
    duplicate_check_passed = BooleanField(default=True)

    # Détails des vérifications
    validation_details = DictField(default=dict)
    rejection_reason = StringField(max_length=500)
    validated_by = StringField(max_length=255)  # Qui a validé/rejeté
    validated_at = DateTimeField(null=True)

    # Informations supplémentaires
    user_agent = StringField(max_length=500)
    location_data = DictField(default=dict)

    meta = {
        'collection': 'registration_validations',
        'ordering': ['-registration_date'],
        'indexes': [
            'username',
            'email',
            'validation_status',
            'registration_date',
            'client_type'
        ]
    }

    def __str__(self):
        return f"Registration validation for {self.username} - {self.validation_status}"


class SecurityAlert(Document):
    """
    Modèle pour les alertes de sécurité concernant les connexions invalides
    et les tentatives frauduleuses.
    """
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    alert_type = StringField(max_length=50, required=True, choices=[
        ('brute_force', 'Brute Force Attack'),
        ('suspicious_login', 'Suspicious Login'),
        ('invalid_credentials', 'Invalid Credentials'),
        ('blocked_ip', 'Blocked IP'),
        ('multiple_failures', 'Multiple Login Failures'),
        ('suspicious_registration', 'Suspicious Registration'),
        ('duplicate_account', 'Duplicate Account Attempt'),
        ('weak_password', 'Weak Password'),
        ('other', 'Other'),
    ])
    severity = StringField(
        max_length=20,
        choices=ALERT_SEVERITY_CHOICES,
        default=ALERT_SEVERITY_MEDIUM
    )
    title = StringField(max_length=255, required=True)
    description = StringField(required=True)
    ip_address = StringField(required=True)
    username = StringField(max_length=255)
    timestamp = DateTimeField(default=datetime.now(timezone.utc))

    # Détails de l'alerte
    related_attempts_count = IntField(default=1)
    alert_details = DictField(default=dict)

    # État de l'alerte
    is_resolved = BooleanField(default=False)
    resolved_at = DateTimeField(null=True)
    resolved_by = StringField(max_length=255)
    resolution_notes = StringField(max_length=1000)

    # Actions prises
    actions_taken = DictField(default=dict)
    auto_blocked = BooleanField(default=False)

    meta = {
        'collection': 'security_alerts',
        'ordering': ['-timestamp'],
        'indexes': [
            'alert_type',
            'severity',
            'ip_address',
            'username',
            'timestamp',
            'is_resolved'
        ]
    }

    def __str__(self):
        return f"{self.alert_type} - {self.severity} - {self.ip_address}"


class IPBlacklist(Document):
    """
    Modèle pour gérer la liste noire des adresses IP.
    Bloque automatiquement les IPs suspectes ou malveillantes.
    """
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    ip_address = StringField(unique=True, required=True)
    reason = StringField(max_length=500, required=True)
    blocked_at = DateTimeField(default=datetime.now(timezone.utc))
    blocked_by = StringField(max_length=255)  # 'auto' ou nom de l'admin

    # Durée du blocage
    is_permanent = BooleanField(default=False)
    expires_at = DateTimeField(null=True)

    # Statistiques
    failed_attempts_count = IntField(default=0)
    last_attempt_at = DateTimeField(null=True)

    # Détails supplémentaires
    location_data = DictField(default=dict)
    notes = StringField(max_length=1000)

    # État actif/inactif
    is_active = BooleanField(default=True)

    meta = {
        'collection': 'ip_blacklist',
        'ordering': ['-blocked_at'],
        'indexes': [
            'ip_address',
            'is_active',
            'expires_at',
            'blocked_at'
        ]
    }

    def __str__(self):
        return f"Blocked IP: {self.ip_address} - {self.reason}"


class RateLimitTracker(Document):
    """
    Modèle pour suivre les limites de taux (rate limiting) par IP.
    Aide à prévenir les attaques par force brute.
    """
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    ip_address = StringField(unique=True, required=True)

    # Compteurs
    login_attempts_count = IntField(default=0)
    registration_attempts_count = IntField(default=0)

    # Fenêtre de temps
    window_start = DateTimeField(default=datetime.now(timezone.utc))
    last_attempt = DateTimeField(default=datetime.now(timezone.utc))

    # Blocage temporaire
    is_temporarily_blocked = BooleanField(default=False)
    block_until = DateTimeField(null=True)

    # Réinitialisation automatique
    reset_at = DateTimeField(null=True)

    meta = {
        'collection': 'rate_limit_tracker',
        'indexes': [
            'ip_address',
            'is_temporarily_blocked',
            'last_attempt'
        ]
    }

    def __str__(self):
        return f"Rate limit for {self.ip_address} - {self.login_attempts_count} attempts"
