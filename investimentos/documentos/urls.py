"""URLs do app documentos (API v1 /api/v1/documentos/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.documentos_list_create, name="documentos_list_create"),
    path("<int:documento_id>/", views.documento_detail, name="documento_detail"),
    path("<int:documento_id>/promover/", views.documento_promover, name="documento_promover"),
]
