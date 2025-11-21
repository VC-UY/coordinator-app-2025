from rest_framework import serializers
from .models import (
    LoginAttempt, RegistrationValidation, SecurityAlert,
    IPBlacklist, RateLimitTracker
)


class LoginAttemptSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    ip_address = serializers.CharField()
    user_agent = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField()
    timestamp = serializers.DateTimeField(read_only=True)
    failure_reason = serializers.CharField(required=False, allow_blank=True)
    location_data = serializers.DictField(required=False)
    is_suspicious = serializers.BooleanField(default=False)
    client_type = serializers.CharField(default='manager')
    manager_ref = serializers.CharField(required=False, allow_null=True)
    volunteer_ref = serializers.CharField(required=False, allow_null=True)

    def create(self, validated_data):
        return LoginAttempt(**validated_data).save()


class RegistrationValidationSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField()
    email = serializers.EmailField()
    ip_address = serializers.CharField()
    registration_date = serializers.DateTimeField(read_only=True)
    validation_status = serializers.CharField(read_only=True)
    client_type = serializers.CharField()
    manager_ref = serializers.CharField(required=False, allow_null=True)
    volunteer_ref = serializers.CharField(required=False, allow_null=True)
    email_valid = serializers.BooleanField(default=False)
    password_strength_score = serializers.IntegerField(default=0)
    ip_reputation_score = serializers.IntegerField(default=50)
    duplicate_check_passed = serializers.BooleanField(default=True)
    validation_details = serializers.DictField(required=False)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    validated_by = serializers.CharField(required=False, allow_blank=True)
    validated_at = serializers.DateTimeField(required=False, allow_null=True)
    user_agent = serializers.CharField(required=False, allow_blank=True)
    location_data = serializers.DictField(required=False)

    def create(self, validated_data):
        return RegistrationValidation(**validated_data).save()

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SecurityAlertSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    alert_type = serializers.CharField()
    severity = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    ip_address = serializers.CharField()
    username = serializers.CharField(required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(read_only=True)
    related_attempts_count = serializers.IntegerField(default=1)
    alert_details = serializers.DictField(required=False)
    is_resolved = serializers.BooleanField(default=False)
    resolved_at = serializers.DateTimeField(required=False, allow_null=True)
    resolved_by = serializers.CharField(required=False, allow_blank=True)
    resolution_notes = serializers.CharField(required=False, allow_blank=True)
    actions_taken = serializers.DictField(required=False)
    auto_blocked = serializers.BooleanField(default=False)

    def create(self, validated_data):
        return SecurityAlert(**validated_data).save()

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class IPBlacklistSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    ip_address = serializers.CharField()
    reason = serializers.CharField()
    blocked_at = serializers.DateTimeField(read_only=True)
    blocked_by = serializers.CharField(required=False, allow_blank=True)
    is_permanent = serializers.BooleanField(default=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    failed_attempts_count = serializers.IntegerField(default=0)
    last_attempt_at = serializers.DateTimeField(required=False, allow_null=True)
    location_data = serializers.DictField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)

    def create(self, validated_data):
        return IPBlacklist(**validated_data).save()

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RateLimitTrackerSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    ip_address = serializers.CharField()
    login_attempts_count = serializers.IntegerField(default=0)
    registration_attempts_count = serializers.IntegerField(default=0)
    window_start = serializers.DateTimeField(read_only=True)
    last_attempt = serializers.DateTimeField(read_only=True)
    is_temporarily_blocked = serializers.BooleanField(default=False)
    block_until = serializers.DateTimeField(required=False, allow_null=True)
    reset_at = serializers.DateTimeField(required=False, allow_null=True)

    def create(self, validated_data):
        return RateLimitTracker(**validated_data).save()

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
