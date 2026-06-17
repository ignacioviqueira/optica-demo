from django.shortcuts import get_object_or_404, render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cuentas.decorators import login_requerido
from apps.inventario.models import Producto

from .models import EventoVTO

# 4 estilos de armazón disponibles como overlay VTO
FRAMES_VTO = {
    'clasico':   {'label': 'Clásico',   'static_path': 'vto/frames/clasico.png'},
    'aviador':   {'label': 'Aviador',   'static_path': 'vto/frames/aviador.png'},
    'redondo':   {'label': 'Redondo',   'static_path': 'vto/frames/redondo.png'},
    'deportivo': {'label': 'Deportivo', 'static_path': 'vto/frames/deportivo.png'},
}


@login_requerido
def index(request):
    """
    GET /vto/?producto=<id>
    Pantalla de Prueba Virtual. Si se pasa ?producto=<id> pre-carga ese armazón.
    """
    producto_id = request.GET.get('producto')
    producto = None
    if producto_id:
        producto = get_object_or_404(Producto, pk=producto_id, activo=True)

    return render(request, 'vto/index.html', {
        'producto': producto,
        'frames_disponibles': FRAMES_VTO,
    })


class RegistrarEventoVTOView(APIView):
    """
    POST /api/vto/evento/
    Registra un evento de conversión VTO → carrito (HU-13).
    Body JSON: { "producto_id": <int> }
    """

    def post(self, request):
        if request.user.rol != 'cliente':
            return Response(
                {'error': 'Solo los clientes pueden registrar eventos VTO'},
                status=status.HTTP_403_FORBIDDEN,
            )

        producto_id = request.data.get('producto_id')
        if not producto_id:
            return Response(
                {'error': 'producto_id requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            producto = Producto.objects.get(pk=producto_id, activo=True)
        except Producto.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND,
            )

        evento = EventoVTO.objects.create(usuario=request.user, producto=producto)
        return Response(
            {'id': evento.pk, 'timestamp': evento.timestamp.isoformat()},
            status=status.HTTP_201_CREATED,
        )
