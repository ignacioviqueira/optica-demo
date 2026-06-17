from django.urls import path

from .api_views import (
    CategoriaListAPIView,
    FiltrosMetaAPIView,
    ProductoDetailAPIView,
    ProductoListAPIView,
)

urlpatterns = [
    path("productos/", ProductoListAPIView.as_view(), name="api-productos"),
    path("productos/<int:pk>/", ProductoDetailAPIView.as_view(), name="api-producto-detalle"),
    path("categorias/", CategoriaListAPIView.as_view(), name="api-categorias"),
    path("filtros/", FiltrosMetaAPIView.as_view(), name="api-filtros"),
]
