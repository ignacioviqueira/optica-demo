from django.urls import path

from .views import MarcarListoView, RechazarPedidoView, ValidarPedidoView

urlpatterns = [
    path("pedidos/<int:pk>/validar/", ValidarPedidoView.as_view(), name="pedido-validar"),
    path("pedidos/<int:pk>/rechazar/", RechazarPedidoView.as_view(), name="pedido-rechazar"),
    path("pedidos/<int:pk>/listo/", MarcarListoView.as_view(), name="pedido-listo"),
]
