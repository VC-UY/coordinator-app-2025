import os

from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Manager


class InternalManagerSyncView(APIView):
    """Synchronise un manager depuis l'app Manager (token interne partage)."""

    permission_classes = [AllowAny]

    def post(self, request):
        expected = os.environ.get('COORDINATOR_INTERNAL_TOKEN', '').strip()
        provided = request.headers.get('X-Internal-Token', '').strip()
        if not expected or provided != expected:
            return Response({'detail': 'Acces refuse.'}, status=status.HTTP_403_FORBIDDEN)

        username = str(request.data.get('username', '')).strip()
        email = str(request.data.get('email', '')).strip().lower()
        password = str(request.data.get('password', '')).strip()
        first_name = str(request.data.get('first_name', '')).strip()
        last_name = str(request.data.get('last_name', '')).strip()

        if not username or not email:
            return Response(
                {'detail': 'username et email sont requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        manager = Manager.objects(email=email).first()
        if manager:
            manager.username = username
            manager.first_name = first_name or manager.first_name
            manager.last_name = last_name or manager.last_name
            if password:
                manager.password = make_password(password)
            manager.status = 'active'
            manager.save()
            created = False
        else:
            manager = Manager(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=make_password(password or email),
                status='active',
            )
            manager.save()
            created = True

        return Response(
            {
                'status': 'success',
                'created': created,
                'manager_id': str(manager.id),
                'username': manager.username,
                'email': manager.email,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
