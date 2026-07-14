"""API prédictions de disponibilité (sonde coordinateur ↔ agent 15 min)."""
from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import APIView


class AvailabilityPredictionsView(APIView):
    """
    GET /api/availability-predictions/
    Historique Redis des sondes + dernière prédiction par volontaire.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        from redis_communication.availability_probe import (
            list_last_probes_by_volunteer,
            list_recent_probes,
        )

        limit = int(request.query_params.get("limit") or 50)
        return Response(
            {
                "latest_by_volunteer": list_last_probes_by_volunteer(),
                "history": list_recent_probes(limit=limit),
                "fields": {
                    "launch": "Oui / non : autoriser un job (+15 min)",
                    "hybrid": "Score final 0–1 (décision vs launch_threshold ≈ 0,32)",
                    "linear": "Score branche ARX",
                    "gru": "Score branche GRU",
                    "horizon_min": "Fenêtre de prédiction (15 min)",
                    "launch_threshold": "Seuil utilisé pour launch",
                    "label": "stay_soft_15m (reste dispo ≥80 % sur 15 min)",
                    "cpu_percent_current": "CPU instantané (%)",
                    "ram_percent_used_current": "RAM utilisée instantanée (%)",
                    "cpu_percent_avg_15m": "CPU moyen fenêtre 15 min (%)",
                    "ram_percent_used_avg_15m": "RAM moyenne fenêtre 15 min (%)",
                    "samples_15m": "Nombre de points dans la fenêtre",
                },
            }
        )


class AvailabilityProbeNowView(APIView):
    """POST /api/availability-predictions/probe/ {volunteer_id} → sonde immédiate."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from redis_communication.availability_probe import probe_volunteer_availability

        vid = str((request.data or {}).get("volunteer_id") or "").strip()
        if not vid:
            return Response({"detail": "volunteer_id requis"}, status=400)
        result = probe_volunteer_availability(vid, horizon_min=15)
        return Response(result)
