"""URLs do app market_data (API v1 /api/v1/series/ e /api/v1/dados/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("series/", views.series_list, name="series_list"),
    path("series/<int:serie_id>/observacoes/", views.serie_observacoes, name="serie_observacoes"),
    path("series/<int:serie_id>/export.csv", views.serie_export_csv, name="serie_export_csv"),
    path("dados/status/", views.dados_status, name="dados_status"),
    # A spec cita `/dados/status` sem barra final; atendemos as duas formas para
    # o contrato da `aplicacao.md` valer sem depender de APPEND_SLASH.
    path("dados/status", views.dados_status, name="dados_status_sem_barra"),
]
