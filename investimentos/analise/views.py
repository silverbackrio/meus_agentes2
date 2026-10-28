"""
Views do app analise — API v1 /api/v1/analise/.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Cenario, Dossie, Metrica
from .serializers import (
    CenarioSerializer,
    DossieSerializer,
    MetricaSerializer,
)


@api_view(["GET"])
def analise_list(request):
    """GET /analise/ — lista de métricas e cenários."""
    metricas = Metrica.objects.all()
    serializer_metricas = MetricaSerializer(metricas, many=True)
    return Response(serializer_metricas.data)


@api_view(["GET"])
def metricas_list(request):
    """GET /analise/metricas/ — métricas calculadas."""
    metricas = Metrica.objects.all()
    serializer = MetricaSerializer(metricas, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def cenarios_list(request):
    """GET /analise/cenarios/ — cenários de estresse."""
    cenarios = Cenario.objects.all()
    serializer = CenarioSerializer(cenarios, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def dossies_list(request):
    """GET /analise/dossies/ — dossiês datados."""
    dossies = Dossie.objects.all()
    serializer = DossieSerializer(dossies, many=True)
    return Response(serializer.data)
