"""Raiz da API v1 — índice JSON das rotas.

A interface do sistema é o app React; a API é JSON puro. O DRF não serve mais a
página "browsable API" (ver `REST_FRAMEWORK` em `settings/base.py`), então quem
abrir uma rota no navegador recebe JSON — e a raiz recebe este índice, em vez de
uma tela HTML sem estilo.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def api_root(request):
    """GET /api/v1/ — mapa das rotas com método e finalidade."""
    base = request.build_absolute_uri("/api/v1/")
    return Response(
        {
            "api": "investimentos",
            "versao": "v1",
            "formato": "JSON",
            "interface": request.build_absolute_uri("/"),
            "rotas": {
                "series": base + "series/",
                "serie_observacoes": base + "series/{id}/observacoes/",
                "serie_csv": base + "series/{id}/export.csv",
                "dados_status": base + "dados/status/",
                "carteira": base + "carteira/",
                "carteira_classes": base + "carteira/classes/",
                "carteira_posicoes": base + "carteira/posicoes/",
                "carteira_resumo": base + "carteira/resumo/",
                "carteira_operacoes": base + "carteira/operacoes/",
                "analise_metricas": base + "analise/metricas/",
                "analise_cenarios": base + "analise/cenarios/",
                "analise_simular": base + "analise/simular/",
                "analise_dossies": base + "analise/dossies/",
                "comparar": base + "comparar/?ativos=&base=liquida",
                "documentos": base + "documentos/",
            },
            "observacao": "Rotas de escrita exigem POST; GET em rota de escrita responde 405 em JSON.",
        }
    )
