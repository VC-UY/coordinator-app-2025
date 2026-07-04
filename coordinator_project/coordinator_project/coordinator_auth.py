import os

from typing import Optional

from django.core import signing
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

TOKEN_SALT = 'coordinator-dashboard'
TOKEN_MAX_AGE = 60 * 60 * 24 * 7  # 7 jours


def _admin_email():
    return os.environ.get('COORDINATOR_ADMIN_EMAIL', '').strip().lower()


def _admin_password():
    return os.environ.get('COORDINATOR_ADMIN_PASSWORD', '')


def issue_token(email: str) -> str:
    return signing.dumps({'email': email}, salt=TOKEN_SALT)


def verify_token(token: str) -> Optional[dict]:
    try:
        return signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except signing.BadSignature:
        return None


class CoordinatorLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = str(request.data.get('email', '')).strip().lower()
        password = str(request.data.get('password', ''))
        admin_email = _admin_email()
        admin_password = _admin_password()

        if not admin_email or not admin_password:
            return Response(
                {'detail': 'Identifiants coordinateur non configures sur le serveur.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if email != admin_email or password != admin_password:
            return Response({'detail': 'Email ou mot de passe incorrect.'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            'token': issue_token(email),
            'email': email,
            'role': 'coordinator',
        })


class CoordinatorSessionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return Response({'authenticated': False}, status=status.HTTP_401_UNAUTHORIZED)
        payload = verify_token(auth[7:].strip())
        if not payload:
            return Response({'authenticated': False}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'authenticated': True, 'email': payload.get('email')})


class CoordinatorAuthMiddleware:
    """Protege les routes /api/ sauf login et sante systeme."""

    OPEN_PATHS = (
        '/api/auth/login/',
        '/api/auth/session/',
        '/api/system-health/',
        '/api/internal/managers/',
    )

    # Lecture seule pour services internes (site public, manager)
    INTERNAL_READ_PREFIXES = (
        '/api/volunteers/',
        '/api/tasks/',
        '/api/workflows/',
        '/api/managers/',
        '/api/system-health/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if request.method == 'OPTIONS':
            return self.get_response(request)
        if path.startswith('/api/') and not any(path.startswith(p) for p in self.OPEN_PATHS):
            # Token service-to-service (stable, ne depend pas du login dashboard)
            internal = os.environ.get('COORDINATOR_INTERNAL_TOKEN', '').strip()
            provided = (
                request.headers.get('X-Internal-Token', '')
                or request.headers.get('X-Coordinator-Internal-Token', '')
            ).strip()
            if (
                internal
                and provided
                and provided == internal
                and request.method in ('GET', 'HEAD')
                and any(path.startswith(p) for p in self.INTERNAL_READ_PREFIXES)
            ):
                return self.get_response(request)

            auth = request.headers.get('Authorization', '')
            if not auth.startswith('Bearer '):
                return JsonResponse({'detail': 'Authentification requise.'}, status=401)
            if not verify_token(auth[7:].strip()):
                return JsonResponse({'detail': 'Session expiree ou invalide.'}, status=401)
        return self.get_response(request)
