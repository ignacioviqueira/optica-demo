from django.shortcuts import render

from apps.cuentas.decorators import rol_requerido


@rol_requerido("ventas", "gerencia")
def operativo(request):
    return render(request, "pedidos/operativo.html")
