from django.urls import path

from .views import (
    carrito,
    checkout,
    comprobante,
    historial,
    operativo,
    orden_trabajo_pdf,
    pago_simulado,
    pedido_detalle,
)

app_name = "pedidos"

urlpatterns = [
    path("carrito/", carrito, name="carrito"),
    path("checkout/", checkout, name="checkout"),
    path("pago/<int:pedido_id>/", pago_simulado, name="pago_simulado"),
    path("comprobante/<int:pedido_id>/", comprobante, name="comprobante"),
    path("historial/", historial, name="historial"),
    path("operativo/", operativo, name="operativo"),
    path("operativo/<int:pedido_id>/", pedido_detalle, name="pedido_detalle"),
    path("operativo/<int:pedido_id>/orden-trabajo/", orden_trabajo_pdf, name="orden_trabajo_pdf"),
]
