from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/tasks/$', consumers.TaskUpdatesConsumer.as_asgi()),
    re_path(r'ws/workflows/$', consumers.WorkflowUpdatesConsumer.as_asgi()),
]
