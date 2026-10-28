"""URLs do app carteira (API v1 /api/v1/carteira/)."""
from django.urls import path

from . import views

urlpatterns = [
    # views serão criados em seguida
    path("", views.carteira_list, name="carteira_list"),
    path("resumo/", views.carteira_resumo, name="carteira_resumo"),
]
