import datetime
import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.inventario.models import Categoria, Producto
from .models import DetallePedido, Pedido, Receta

User = get_user_model()


def make_user(email="u@test.com", rol="cliente"):
    return User.objects.create_user(
        email=email, username=email.split("@")[0], password="Test@123", rol=rol
    )


def make_categoria():
    return Categoria.objects.create(nombre="Cat Test")


def make_producto(cat, stock=10):
    return Producto.objects.create(
        nombre="Prod Test",
        marca="Marca Test",
        precio=Decimal("10000.00"),
        stock_actual=stock,
        stock_minimo=3,
        categoria=cat,
    )


# ── Modelo Receta ─────────────────────────────────────────────────────────────

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


# ── Modelo Pedido — máquina de estados ───────────────────────────────────────

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

    def test_transicion_a_listo(self):
        pedido = Pedido.objects.create(
            usuario=self.user, total=Decimal("10000.00"), estado=Pedido.Estado.EN_PROCESO
        )
        pedido.estado = Pedido.Estado.LISTO
        pedido.save()
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.Estado.LISTO)


# ── Modelo DetallePedido ──────────────────────────────────────────────────────

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


# ── Checkout view ─────────────────────────────────────────────────────────────

class CheckoutViewTest(TestCase):
    def setUp(self):
        self.cat = make_categoria()
        self.prod = make_producto(self.cat, stock=10)
        self.cliente = make_user("cli@test.com", "cliente")
        self.ventas = make_user("v@test.com", "ventas")
        self.c = Client()

    def _post_checkout(self, user, items):
        self.c.force_login(user)
        return self.c.post(
            reverse("pedidos:checkout"),
            {"carrito_json": json.dumps(items)},
        )

    def test_checkout_crea_pedido_y_detalles(self):
        items = [{"id": self.prod.pk, "nombre": "Prod Test", "precio": "10000", "cantidad": 2}]
        r = self._post_checkout(self.cliente, items)
        self.assertEqual(r.status_code, 302)
        pedido = Pedido.objects.filter(usuario=self.cliente).first()
        self.assertIsNotNone(pedido)
        self.assertEqual(pedido.total, Decimal("20000.00"))
        self.assertEqual(pedido.detalles.count(), 1)
        self.assertEqual(pedido.detalles.first().cantidad, 2)

    def test_checkout_descuenta_stock(self):
        stock_antes = self.prod.stock_actual
        items = [{"id": self.prod.pk, "nombre": "Prod Test", "precio": "10000", "cantidad": 3}]
        self._post_checkout(self.cliente, items)
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock_actual, stock_antes - 3)

    def test_checkout_stock_insuficiente_redirige_con_error(self):
        prod_sin_stock = make_producto(self.cat, stock=1)
        items = [{"id": prod_sin_stock.pk, "nombre": "X", "precio": "10000", "cantidad": 5}]
        r = self._post_checkout(self.cliente, items)
        self.assertRedirects(r, reverse("pedidos:checkout"))
        self.assertEqual(Pedido.objects.filter(usuario=self.cliente).count(), 0)

    def test_checkout_carrito_vacio_redirige(self):
        r = self._post_checkout(self.cliente, [])
        self.assertRedirects(r, reverse("pedidos:checkout"))

    def test_checkout_rol_ventas_redirige(self):
        items = [{"id": self.prod.pk, "nombre": "Prod Test", "precio": "10000", "cantidad": 1}]
        r = self._post_checkout(self.ventas, items)
        self.assertRedirects(r, reverse("catalogo:index"))

    def test_checkout_rol_gerencia_redirige(self):
        gerencia = make_user("ger@test.com", "gerencia")
        items = [{"id": self.prod.pk, "nombre": "Prod Test", "precio": "10000", "cantidad": 1}]
        r = self._post_checkout(gerencia, items)
        self.assertRedirects(r, reverse("catalogo:index"))

    def test_checkout_no_autenticado_redirige_login(self):
        r = self.c.post(
            reverse("pedidos:checkout"),
            {"carrito_json": json.dumps([{"id": self.prod.pk, "precio": "10000", "cantidad": 1}])},
        )
        self.assertEqual(r.status_code, 302)
        self.assertIn("/cuentas/login/", r["Location"])

    def test_checkout_redirige_a_pago_simulado(self):
        items = [{"id": self.prod.pk, "nombre": "Prod Test", "precio": "10000", "cantidad": 1}]
        r = self._post_checkout(self.cliente, items)
        self.assertEqual(r.status_code, 302)
        pedido = Pedido.objects.filter(usuario=self.cliente).first()
        self.assertIn(f"/pedidos/pago/{pedido.pk}/", r["Location"])


# ── API Validar / Rechazar / Listo ────────────────────────────────────────────

class TransicionesPedidoAPITest(TestCase):
    def setUp(self):
        self.cat = make_categoria()
        self.prod = make_producto(self.cat)
        self.cliente = make_user("cli2@test.com", "cliente")
        self.ventas = make_user("ven@test.com", "ventas")
        self.gerencia = make_user("ger@test.com", "gerencia")
        self.c = Client()
        self.pedido = Pedido.objects.create(usuario=self.cliente, total=Decimal("10000.00"))

    def _post(self, user, url_name, pk, body=None):
        self.c.force_login(user)
        return self.c.post(
            reverse(f"pedido-{url_name}", kwargs={"pk": pk}),
            json.dumps(body or {}),
            content_type="application/json",
        )

    def test_validar_cambia_estado_a_en_proceso(self):
        r = self._post(self.ventas, "validar", self.pedido.pk)
        self.assertEqual(r.status_code, 200)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estado.EN_PROCESO)

    def test_gerencia_puede_validar(self):
        r = self._post(self.gerencia, "validar", self.pedido.pk)
        self.assertEqual(r.status_code, 200)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estado.EN_PROCESO)

    def test_gerencia_puede_rechazar(self):
        r = self._post(self.gerencia, "rechazar", self.pedido.pk, {"motivo": "Receta inválida"})
        self.assertEqual(r.status_code, 200)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estado.RECHAZADO)

    def test_validar_solo_ventas_o_gerencia(self):
        r = self._post(self.cliente, "validar", self.pedido.pk)
        self.assertEqual(r.status_code, 403)

    def test_validar_no_pendiente_devuelve_400(self):
        self.pedido.estado = Pedido.Estado.EN_PROCESO
        self.pedido.save()
        r = self._post(self.ventas, "validar", self.pedido.pk)
        self.assertEqual(r.status_code, 400)

    def test_rechazar_cambia_estado_y_guarda_motivo(self):
        r = self._post(self.ventas, "rechazar", self.pedido.pk, {"motivo": "Receta ilegible"})
        self.assertEqual(r.status_code, 200)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estado.RECHAZADO)
        self.assertEqual(self.pedido.motivo_rechazo, "Receta ilegible")

    def test_rechazar_sin_motivo_devuelve_400(self):
        r = self._post(self.ventas, "rechazar", self.pedido.pk, {"motivo": ""})
        self.assertEqual(r.status_code, 400)
        self.pedido.refresh_from_db()
        self.assertNotEqual(self.pedido.estado, Pedido.Estado.RECHAZADO)

    def test_rechazar_solo_ventas_o_gerencia(self):
        r = self._post(self.cliente, "rechazar", self.pedido.pk, {"motivo": "test"})
        self.assertEqual(r.status_code, 403)

    def test_listo_solo_gerencia(self):
        self.pedido.estado = Pedido.Estado.EN_PROCESO
        self.pedido.save()
        r = self._post(self.ventas, "listo", self.pedido.pk)
        self.assertEqual(r.status_code, 403)
        r2 = self._post(self.gerencia, "listo", self.pedido.pk)
        self.assertEqual(r2.status_code, 200)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estado.LISTO)

    def test_listo_requiere_en_proceso(self):
        r = self._post(self.gerencia, "listo", self.pedido.pk)
        self.assertEqual(r.status_code, 400)

    @patch("apps.pedidos.views.notificar_pedido_validado")
    @patch("apps.pedidos.models.Pedido.save", side_effect=RuntimeError("DB error"))
    def test_webhook_no_se_llama_si_pedido_save_falla(self, mock_save, mock_notify):
        # raise_request_exception=False → devuelve 500 en vez de re-lanzar la excepción
        c = Client(raise_request_exception=False)
        c.force_login(self.ventas)
        c.post(
            reverse("pedido-validar", kwargs={"pk": self.pedido.pk}),
            json.dumps({}),
            content_type="application/json",
        )
        mock_notify.assert_not_called()


# ── PDF de orden de trabajo ───────────────────────────────────────────────────

class OrdenTrabajoPDFTest(TestCase):
    def setUp(self):
        self.cat = make_categoria()
        self.prod = make_producto(self.cat)
        self.cliente = make_user("cpdf@test.com", "cliente")
        self.gerencia = make_user("gpdf@test.com", "gerencia")
        self.ventas = make_user("vpdf@test.com", "ventas")
        self.c = Client()
        self.pedido = Pedido.objects.create(
            usuario=self.cliente,
            total=Decimal("10000.00"),
            estado=Pedido.Estado.EN_PROCESO,
        )
        DetallePedido.objects.create(
            pedido=self.pedido, producto=self.prod,
            cantidad=1, precio_unitario=Decimal("10000.00"),
        )

    def test_pdf_devuelve_content_type_pdf(self):
        self.c.force_login(self.gerencia)
        r = self.c.get(reverse("pedidos:orden_trabajo_pdf", kwargs={"pedido_id": self.pedido.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")

    def test_pdf_solo_gerencia(self):
        self.c.force_login(self.ventas)
        r = self.c.get(reverse("pedidos:orden_trabajo_pdf", kwargs={"pedido_id": self.pedido.pk}))
        self.assertEqual(r.status_code, 403)

    def test_pdf_inicia_con_bytes_pdf(self):
        self.c.force_login(self.gerencia)
        r = self.c.get(reverse("pedidos:orden_trabajo_pdf", kwargs={"pedido_id": self.pedido.pk}))
        self.assertTrue(r.content.startswith(b"%PDF"))


# ── Historial ─────────────────────────────────────────────────────────────────

class HistorialTest(TestCase):
    def setUp(self):
        self.cliente = make_user("hcli@test.com", "cliente")
        self.otro_cliente = make_user("hother@test.com", "cliente")
        self.gerencia = make_user("hger@test.com", "gerencia")
        self.c = Client()
        self.p1 = Pedido.objects.create(usuario=self.cliente, total=Decimal("5000.00"))
        self.p2 = Pedido.objects.create(usuario=self.otro_cliente, total=Decimal("8000.00"))

    def test_cliente_solo_ve_sus_pedidos(self):
        self.c.force_login(self.cliente)
        r = self.c.get(reverse("pedidos:historial"))
        self.assertEqual(r.status_code, 200)
        pedidos = list(r.context["pedidos"])
        self.assertIn(self.p1, pedidos)
        self.assertNotIn(self.p2, pedidos)

    def test_gerencia_ve_todos_los_pedidos(self):
        self.c.force_login(self.gerencia)
        r = self.c.get(reverse("pedidos:historial"))
        self.assertEqual(r.status_code, 200)
        pedidos = list(r.context["pedidos"])
        self.assertIn(self.p1, pedidos)
        self.assertIn(self.p2, pedidos)

    def test_gerencia_puede_buscar_por_email(self):
        self.c.force_login(self.gerencia)
        r = self.c.get(reverse("pedidos:historial") + "?q=hother")
        pedidos = list(r.context["pedidos"])
        self.assertIn(self.p2, pedidos)
        self.assertNotIn(self.p1, pedidos)

    def test_historial_requiere_autenticacion(self):
        r = self.c.get(reverse("pedidos:historial"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/cuentas/login/", r["Location"])

    def test_historial_ventas_no_tiene_acceso(self):
        ventas = make_user("hven@test.com", "ventas")
        self.c.force_login(ventas)
        r = self.c.get(reverse("pedidos:historial"))
        self.assertEqual(r.status_code, 403)
