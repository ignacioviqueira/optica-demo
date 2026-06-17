from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.cuentas.decorators import rol_requerido

from .forms import ProductoForm
from .models import Producto


@rol_requerido("gerencia")
def lista(request):
    productos = Producto.objects.select_related("categoria").order_by("activo", "categoria", "marca", "nombre")
    criticos = sum(1 for p in productos if p.activo and p.stock_critico)
    return render(request, "inventario/lista.html", {"productos": productos, "criticos": criticos})


@rol_requerido("gerencia")
def nuevo(request):
    form = ProductoForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Producto creado correctamente.")
        return redirect("inventario:lista")
    return render(request, "inventario/form.html", {"form": form, "titulo": "Nuevo producto"})


@rol_requerido("gerencia")
def editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, request.FILES or None, instance=producto)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"«{producto}» actualizado correctamente.")
        return redirect("inventario:lista")
    return render(request, "inventario/form.html", {"form": form, "titulo": f"Editar — {producto}", "producto": producto})


@rol_requerido("gerencia")
def toggle_activo(request, pk):
    """Baja lógica / reactivación: POST only."""
    if request.method != "POST":
        return redirect("inventario:lista")
    producto = get_object_or_404(Producto, pk=pk)
    producto.activo = not producto.activo
    producto.save(update_fields=["activo"])
    accion = "activado" if producto.activo else "dado de baja"
    messages.success(request, f"«{producto}» {accion} correctamente.")
    return redirect("inventario:lista")
