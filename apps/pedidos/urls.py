from django.urls import path

from .views import carrito, operativo

app_name = "pedidos"

urlpatterns = [
    path("operativo/", operativo, name="operativo"),
    path("carrito/", carrito, name="carrito"),
]
