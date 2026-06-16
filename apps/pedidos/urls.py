from django.urls import path

from .views import operativo

app_name = "pedidos"

urlpatterns = [
    path("operativo/", operativo, name="operativo"),
]
