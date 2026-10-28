"""
Views do app carteira — API v1 /api/v1/carteira/.
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Posicao
from .serializers import (
    PosicaoSerializer,
)


@api_view(["GET"])
def carteira_list(request):
    """GET /carteira/ — lista de posições de carteira."""
    posicoes = Posicao.objects.all()
    serializer = PosicaoSerializer(posicoes, many=True)
    return Response(serializer.data)


@api_view(["GET", "POST"])
def carteira_resumo(request):
    """GET /carteira/resumo/ — resumo da carteira do usuário."""
    if request.method == "GET":
        posicoes = Posicao.objects.all()
        serializer = PosicaoSerializer(posicoes, many=True)
        return Response(serializer.data)
    return Response({"erro": "Método não permitido."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
