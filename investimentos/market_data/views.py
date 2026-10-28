"""
Views do app market_data — API v1 /api/v1/.
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import FetchLog, Observation, Serie, Source
from .serializers import (
    FetchLogSerializer,
    ObservationSerializer,
    SerieSerializer,
    SourceSerializer,
)


@api_view(["GET"])
def series_list(request):
    """GET /series/ — lista de séries com cobertura e as_of."""
    series = Serie.objects.all()
    serializer = SerieSerializer(series, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def series_detail(request, pk):
    """GET /series/{id}/ — detalhe de uma série."""
    serie = get_object_or_404(Serie, pk=pk)
    serializer = SerieSerializer(serie)
    return Response(serializer.data)


@api_view(["GET"])
def observacoes_list(request, pk):
    """GET /series/{pk}/observacoes/ — observações de uma série."""
    serie = get_object_or_404(Serie, pk=pk)
    observacoes = Observation.objects.filter(serie=serie)
    serializer = ObservationSerializer(observacoes, many=True)
    return Response(serializer.data)


@api_view(["GET", "POST"])
def dados_status(request):
    """GET /dados/status — cobertura por fonte, fetch_log do dia, cota."""
    if request.method == "GET":
        sources = Source.objects.all()
        serializer_sources = SourceSerializer(sources, many=True)
        fetch_logs_recent = FetchLog.objects.order_by("-dia")[:10]
        serializer_logs = FetchLogSerializer(fetch_logs_recent, many=True)
        return Response({
            "sources": serializer_sources.data,
            "logs_recentes": serializer_logs.data,
        })
    return Response({"erro": "Método não permitido."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
