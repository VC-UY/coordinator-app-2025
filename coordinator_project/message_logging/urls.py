from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageLogViewSet

router = DefaultRouter()
router.register(r'logs', MessageLogViewSet, basename='messagelog')

urlpatterns = [
    path('', include(router.urls)),
]
