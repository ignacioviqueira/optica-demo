from django.urls import path

from . import views

app_name = "inventario"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.nuevo, name="nuevo"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/toggle/", views.toggle_activo, name="toggle"),
]
