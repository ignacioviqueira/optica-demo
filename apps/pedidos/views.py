from django.shortcuts import render

from apps.cuentas.decorators import login_requerido, rol_requerido


@rol_requerido("ventas", "gerencia")
def operativo(request):
    return render(request, "pedidos/operativo.html")


@login_requerido
def carrito(request):
    return render(request, "pedidos/carrito.html")
