import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.inventario.models import Categoria, Producto
from .models import DetallePedido, Pedido, Receta

User = get_user_model()


def make_user(email="u@test.com"):
    return User.objects.create_user(email=email, username=email.split("@")[0], password="Test@123")


def make_categoria():
    return Categoria.objects.create(nombre="Cat Test")


def make_producto(cat):
    return Producto.objects.create(
        nombre="Prod Test",
        marca="Marca Test",
        precio=Decimal("10000.00"),
        stock_actual=10,
        stock_minimo=3,
        categoria=cat,
    )


class RecetaTest(TestCase):
    def test_str_contiene_usuario_y_fecha(self):
        user = make_user()
        receta = Receta.objects.create(
            usuario=user,
            esfera_od=Decimal("-2.50"),
            cilindro_od=Decimal("-0.75"),
            eje_od=170,
            dnp=Decimal("64.00"),
            fecha_emision=datetime.date(2025, 1, 15),
        )
        self.assertIn(str(user), str(receta))
        self.assertIn("2025", str(receta))


class PedidoTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_estado_default_es_pendiente_validacion(self):
        pedido = Pedido.objects.create(usuario=self.user, total=Decimal("10000.00"))
        self.assertEqual(pedido.estado, Pedido.Estado.PENDIENTE_VALIDACION)

    def test_transicion_a_en_proceso(self):
        pedido = Pedido.objects.create(usuario=self.user, total=Decimal("10000.00"))
        pedido.estado = Pedido.Estado.EN_PROCESO
        pedido.save()
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.Estado.EN_PROCESO)

    def test_transicion_a_rechazado_guarda_motivo(self):
        pedido = Pedido.objects.create(usuario=self.user, total=Decimal("10000.00"))
        pedido.estado = Pedido.Estado.RECHAZADO
        pedido.motivo_rechazo = "Receta vencida"
        pedido.save()
        pedido.refresh_from_db()
        self.assertEqual(pedido.motivo_rechazo, "Receta vencida")


class DetallePedidoTest(TestCase):
    def setUp(self):
        self.user = make_user("d@test.com")
        cat = make_categoria()
        self.prod = make_producto(cat)
        self.pedido = Pedido.objects.create(usuario=self.user, total=Decimal("20000.00"))

    def test_subtotal_calcula_correctamente(self):
        detalle = DetallePedido.objects.create(
            pedido=self.pedido,
            producto=self.prod,
            cantidad=2,
            precio_unitario=Decimal("10000.00"),
        )
        self.assertEqual(detalle.subtotal, Decimal("20000.00"))

    def test_subtotal_con_cantidad_uno(self):
        detalle = DetallePedido.objects.create(
            pedido=self.pedido,
            producto=self.prod,
            cantidad=1,
            precio_unitario=Decimal("38000.00"),
        )
        self.assertEqual(detalle.subtotal, Decimal("38000.00"))
