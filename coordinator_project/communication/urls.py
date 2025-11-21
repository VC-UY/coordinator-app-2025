"""
URLs pour l'application de communication.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CommunicationViewSet, LogViewSet, AnnouncementViewSet,
    CommunicationStatsView
)

app_name = 'communication'

router = DefaultRouter()
router.register(r'logs', LogViewSet, basename='log')
router.register(r'announcements', AnnouncementViewSet, basename='announcement')

urlpatterns = [
    path('stats/', CommunicationStatsView.as_view(), name='communication-stats'),
]

urlpatterns += router.urls
