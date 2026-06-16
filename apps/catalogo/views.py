from django.shortcuts import render

from apps.cuentas.decorators import login_requerido


def home(request):
    return render(request, "home.html")


@login_requerido
def index(request):
    return render(request, "catalogo/index.html")
