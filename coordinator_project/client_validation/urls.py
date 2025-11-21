from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginAttemptViewSet, RegistrationValidationViewSet,
    SecurityAlertViewSet, IPBlacklistViewSet, ValidationStatsView
)

router = DefaultRouter()
router.register(r'login-attempts', LoginAttemptViewSet, basename='login-attempt')
router.register(r'registrations', RegistrationValidationViewSet, basename='registration-validation')
router.register(r'security-alerts', SecurityAlertViewSet, basename='security-alert')
router.register(r'ip-blacklist', IPBlacklistViewSet, basename='ip-blacklist')

urlpatterns = [
    path('validation/stats/', ValidationStatsView.as_view(), name='validation-stats'),
]

urlpatterns += router.urls
