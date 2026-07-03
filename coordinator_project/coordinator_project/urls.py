from django.contrib import admin
from django.urls import path, include
from coordinator_project.coordinator_auth import CoordinatorLoginView, CoordinatorSessionView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', CoordinatorLoginView.as_view(), name='coordinator-login'),
    path('api/auth/session/', CoordinatorSessionView.as_view(), name='coordinator-session'),
    path('api/', include('manager.urls')),
    path('api/', include('volunteer.urls')),
    path('api/', include('communication.urls')),
    path('api/', include('client_validation.urls')),
    path('api/logs/', include('message_logging.urls')),
]
