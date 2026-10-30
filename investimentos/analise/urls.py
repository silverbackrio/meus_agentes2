"""URLs do app analise (API v1 /api/v1/analise/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.analise_list, name="analise_list"),
    path("metricas/", views.metricas_list, name="metricas_list"),
    path("cenarios/", views.cenarios_list, name="cenarios_list"),
    path("dossies/", views.dossies_list, name="dossies_list"),
    # Contrato da aplicacao.md cita `/analise/dossies/{data}` sem barra final;
    # atendemos as duas formas como market_data faz com `/dados/status`.
    path("dossies/<str:data>/", views.dossie_detail, name="dossie_detail"),
    path("dossies/<str:data>", views.dossie_detail, name="dossie_detail_sem_barra"),
    path("simular/", views.simular, name="analise_simular"),
]
