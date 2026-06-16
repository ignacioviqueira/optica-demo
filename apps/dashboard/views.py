from django.shortcuts import render

from apps.cuentas.decorators import rol_requerido


@rol_requerido("gerencia")
def index(request):
    return render(request, "dashboard/index.html")
