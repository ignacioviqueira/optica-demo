from django.shortcuts import get_object_or_404, render

from apps.cuentas.decorators import login_requerido
from apps.inventario.models import Producto


def home(request):
    return render(request, "home.html")


@login_requerido
def index(request):
    return render(request, "catalogo/index.html")


@login_requerido
def detalle(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    return render(request, "catalogo/detalle.html", {"producto": producto})
