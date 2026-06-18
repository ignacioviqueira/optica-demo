import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cuentas.decorators import login_requerido, rol_requerido
from apps.inventario.models import Producto

from .models import DetallePedido, Pedido, Receta
from .pdf_utils import generar_orden_trabajo


# ── Vistas HTML ────────────────────────────────────────────────────────────────

@login_requerido
def carrito(request):
    return render(request, "pedidos/carrito.html")


@login_requerido
def checkout(request):
    if request.user.rol != "cliente":
        messages.error(request, "Solo los clientes pueden realizar pedidos.")
        return redirect("catalogo:index")

    if request.method == "POST":
        carrito_json = request.POST.get("carrito_json", "[]")
        try:
            items = json.loads(carrito_json)
        except (json.JSONDecodeError, ValueError):
            messages.error(request, "Error al procesar el carrito.")
            return redirect("pedidos:checkout")

        if not items:
            messages.error(request, "El carrito está vacío.")
            return redirect("pedidos:checkout")

        try:
            with transaction.atomic():
                validated = []
                for item in items:
                    prod = get_object_or_404(Producto, pk=item["id"], activo=True)
                    cantidad = max(1, int(item.get("cantidad", 1)))
                    try:
                        precio = Decimal(str(item["precio"]))
                    except (InvalidOperation, KeyError):
                        raise ValueError(f"Precio inválido para {prod.nombre}")
                    if prod.stock_actual < cantidad:
                        raise ValueError(f"Stock insuficiente para {prod.nombre}.")
                    validated.append((prod, cantidad, precio))

                total = sum(p * c for _, c, p in validated)
                pedido = Pedido.objects.create(usuario=request.user, total=total)

                for prod, cantidad, precio in validated:
                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=prod,
                        cantidad=cantidad,
                        precio_unitario=precio,
                    )
                    prod.descontar_stock(cantidad)

                if "receta_imagen" in request.FILES:
                    pedido.receta_imagen = request.FILES["receta_imagen"]
                    pedido.save()

        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("pedidos:checkout")
        except Exception:
            messages.error(request, "No se pudo procesar el pedido. Intentá de nuevo.")
            return redirect("pedidos:checkout")

        return redirect("pedidos:pago_simulado", pedido_id=pedido.pk)

    return render(request, "pedidos/checkout.html")


@login_requerido
def pago_simulado(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id, usuario=request.user)
    if request.method == "POST":
        return redirect("pedidos:comprobante", pedido_id=pedido.pk)
    return render(request, "pedidos/pago_simulado.html", {"pedido": pedido})


@login_requerido
def comprobante(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id, usuario=request.user)
    return render(request, "pedidos/comprobante.html", {"pedido": pedido})


@rol_requerido("cliente", "gerencia")
def historial(request):
    if request.user.rol == "gerencia":
        q = request.GET.get("q", "").strip()
        pedidos = Pedido.objects.select_related("usuario").prefetch_related("detalles")
        if q:
            pedidos = pedidos.filter(usuario__email__icontains=q)
        else:
            pedidos = pedidos.all()
        return render(request, "pedidos/historial.html", {"pedidos": pedidos, "q": q})

    pedidos = (
        Pedido.objects.filter(usuario=request.user)
        .prefetch_related("detalles__producto")
    )
    return render(request, "pedidos/historial.html", {"pedidos": pedidos})


@rol_requerido("ventas", "gerencia")
def operativo(request):
    estado_filtro = request.GET.get("estado", "")
    q = request.GET.get("q", "").strip()

    pedidos = Pedido.objects.select_related("usuario").prefetch_related("detalles")
    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)
    if q:
        pedidos = pedidos.filter(usuario__email__icontains=q)

    # Contadores por estado para las pestañas
    contadores = {
        Pedido.Estado.PENDIENTE_VALIDACION: Pedido.objects.filter(
            estado=Pedido.Estado.PENDIENTE_VALIDACION
        ).count(),
        Pedido.Estado.EN_PROCESO: Pedido.objects.filter(
            estado=Pedido.Estado.EN_PROCESO
        ).count(),
        Pedido.Estado.LISTO: Pedido.objects.filter(estado=Pedido.Estado.LISTO).count(),
        Pedido.Estado.RECHAZADO: Pedido.objects.filter(
            estado=Pedido.Estado.RECHAZADO
        ).count(),
    }

    return render(
        request,
        "pedidos/operativo.html",
        {
            "pedidos": pedidos,
            "estado_filtro": estado_filtro,
            "q": q,
            "contadores": contadores,
            "estados": Pedido.Estado,
        },
    )


@rol_requerido("ventas", "gerencia")
def pedido_detalle(request, pedido_id):
    pedido = get_object_or_404(
        Pedido.objects.select_related("usuario", "receta").prefetch_related("detalles__producto"),
        pk=pedido_id,
    )
    return render(request, "pedidos/pedido_detalle.html", {"pedido": pedido})


@rol_requerido("gerencia")
def orden_trabajo_pdf(request, pedido_id):
    pedido = get_object_or_404(
        Pedido.objects.select_related("usuario", "receta").prefetch_related("detalles__producto"),
        pk=pedido_id,
    )
    pdf_bytes = generar_orden_trabajo(pedido)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="orden_trabajo_{pedido.pk}.pdf"'
    )
    return response


# ── API DRF ────────────────────────────────────────────────────────────────────

class ValidarPedidoView(APIView):
    """
    POST /api/pedidos/<pk>/validar/
    Ventas o Gerencia valida un pedido: PENDIENTE_VALIDACION → EN_PROCESO
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.rol not in ("ventas", "gerencia"):
            return Response(
                {"error": "Acción reservada para ventas o gerencia"},
                status=status.HTTP_403_FORBIDDEN,
            )
        pedido = get_object_or_404(Pedido, pk=pk)
        if pedido.estado != Pedido.Estado.PENDIENTE_VALIDACION:
            return Response(
                {"error": "Solo se pueden validar pedidos pendientes"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pedido.estado = Pedido.Estado.EN_PROCESO
        pedido.save()
        return Response({"estado": pedido.get_estado_display()})


class RechazarPedidoView(APIView):
    """
    POST /api/pedidos/<pk>/rechazar/
    Body: { "motivo": "..." }
    Ventas rechaza un pedido y dispara email simulado al cliente.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.rol not in ("ventas", "gerencia"):
            return Response(
                {"error": "Acción reservada para ventas o gerencia"},
                status=status.HTTP_403_FORBIDDEN,
            )
        pedido = get_object_or_404(Pedido, pk=pk)
        if pedido.estado != Pedido.Estado.PENDIENTE_VALIDACION:
            return Response(
                {"error": "Solo se pueden rechazar pedidos pendientes"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        motivo = (request.data.get("motivo") or "").strip()
        if not motivo:
            return Response(
                {"error": "El motivo de rechazo es obligatorio"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pedido.estado = Pedido.Estado.RECHAZADO
        pedido.motivo_rechazo = motivo
        pedido.save()

        # Email simulado (imprime en stdout del contenedor en entorno dev)
        send_mail(
            subject=f"Pedido #{pedido.pk} rechazado — Óptica Demo",
            message=(
                f"Hola {pedido.usuario.get_full_name() or pedido.usuario.email},\n\n"
                f"Tu pedido #{pedido.pk} fue rechazado por el siguiente motivo:\n"
                f"{motivo}\n\n"
                "Por favor, contactate con nosotros para más información.\n\n"
                "Óptica Demo"
            ),
            from_email=None,
            recipient_list=[pedido.usuario.email],
            fail_silently=True,
        )

        return Response({"estado": pedido.get_estado_display()})


class MarcarListoView(APIView):
    """
    POST /api/pedidos/<pk>/listo/
    Gerencia marca el pedido como listo: EN_PROCESO → LISTO
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.rol != "gerencia":
            return Response(
                {"error": "Acción reservada para gerencia"},
                status=status.HTTP_403_FORBIDDEN,
            )
        pedido = get_object_or_404(Pedido, pk=pk)
        if pedido.estado != Pedido.Estado.EN_PROCESO:
            return Response(
                {"error": "Solo se pueden marcar como listos pedidos en proceso"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pedido.estado = Pedido.Estado.LISTO
        pedido.save()
        return Response({"estado": pedido.get_estado_display()})
