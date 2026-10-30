"""URL declarations do investimentos_project.

API v1: /api/v1/
"""

from django.contrib import admin
from django.urls import include, path

from investimentos.analise.views import comparar

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("investimentos.market_data.urls")),
    path("api/v1/carteira/", include("investimentos.carteira.urls")),
    path("api/v1/analise/", include("investimentos.analise.urls")),
    # `/comparar` é de nível raiz no contrato da aplicacao.md (fora do prefixo
    # /analise/), por isso a rota é declarada aqui, no project.
    path("api/v1/comparar/", comparar, name="comparar"),
    path("api/v1/comparar", comparar, name="comparar_sem_barra"),
]
