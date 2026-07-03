from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('manager.urls')),
    path('api/', include('volunteer.urls')),
    path('api/', include('communication.urls')),
    path('api/', include('client_validation.urls')),
    path('api/logs/', include('message_logging.urls')),
]
