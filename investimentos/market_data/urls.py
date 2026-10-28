"""URLs do app market_data (API v1 /api/v1/market_data/)."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.series_list, name="series_list"),
    path("<int:pk>/", views.series_detail, name="series_detail"),
    path("<int:pk>/observacoes/", views.observacoes_list, name="observacoes_list"),
    path("status/", views.dados_status, name="dados_status"),
]
