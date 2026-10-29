"""URL declarations do investimentos_project.

API v1: /api/v1/
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("investimentos.market_data.urls")),
    path("api/v1/carteira/", include("investimentos.carteira.urls")),
    path("api/v1/analise/", include("investimentos.analise.urls")),
]
