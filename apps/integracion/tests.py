from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.integracion.webhooks import (
    _post_webhook,
    notificar_pedido_validado,
    notificar_stock_critico,
)
from apps.inventario.models import Categoria, Producto
from apps.pedidos.models import Pedido

User = get_user_model()


def make_user(email="w@test.com", rol="cliente"):
    return User.objects.create_user(
        email=email, username=email.split("@")[0], password="Test@123", rol=rol
    )


def make_producto():
    cat = Categoria.objects.create(nombre="Cat Integracion")
    return Producto.objects.create(
        nombre="Frame Test", marca="Marca", precio=Decimal("10000"),
        stock_actual=3, stock_minimo=3, categoria=cat,
    )


# ── _post_webhook ──────────────────────────────────────────────────────────────

class PostWebhookTest(TestCase):

    @override_settings(N8N_WEBHOOK_BASE="http://n8n-test:5678/webhook")
    @patch("apps.integracion.webhooks.requests.post")
    def test_llama_a_url_correcta(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        _post_webhook("mi-path", {"clave": "valor"})
        mock_post.assert_called_once()
        url_llamada = mock_post.call_args[0][0]
        self.assertIn("mi-path", url_llamada)
        self.assertIn("n8n-test", url_llamada)

    @override_settings(N8N_WEBHOOK_BASE="")
    @patch("apps.integracion.webhooks.requests.post")
    def test_omite_llamada_si_base_vacia(self, mock_post):
        _post_webhook("alguna-ruta", {})
        mock_post.assert_not_called()

    @override_settings(N8N_WEBHOOK_BASE="http://n8n-test:5678/webhook")
    @patch("apps.integracion.webhooks.requests.post")
    def test_falla_silenciosamente_en_connection_error(self, mock_post):
        import requests as req
        mock_post.side_effect = req.exceptions.ConnectionError("n8n down")
        # No debe lanzar excepción
        _post_webhook("mi-path", {})

    @override_settings(N8N_WEBHOOK_BASE="http://n8n-test:5678/webhook")
    @patch("apps.integracion.webhooks.requests.post")
    def test_falla_silenciosamente_en_timeout(self, mock_post):
        import requests as req
        mock_post.side_effect = req.exceptions.Timeout()
        _post_webhook("mi-path", {})


# ── notificar_pedido_validado ──────────────────────────────────────────────────

class NotificarPedidoValidadoTest(TestCase):

    def setUp(self):
        self.user = make_user("nv@test.com")
        self.pedido = Pedido.objects.create(
            usuario=self.user,
            total=Decimal("25000"),
            estado=Pedido.Estado.EN_PROCESO,
        )

    @override_settings(N8N_WEBHOOK_BASE="http://n8n-test:5678/webhook")
    @patch("apps.integracion.webhooks.requests.post")
    def test_envia_payload_correcto(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        notificar_pedido_validado(self.pedido)
        mock_post.assert_called_once()
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["pedido_id"], self.pedido.pk)
        self.assertEqual(payload["usuario_email"], self.user.email)
        self.assertIn("total", payload)
        self.assertIn("estado", payload)

    @override_settings(N8N_WEBHOOK_BASE="http://n8n-test:5678/webhook")
    @patch("apps.integracion.webhooks.requests.post")
    def test_llama_a_ruta_pedido_validado(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        notificar_pedido_validado(self.pedido)
        url = mock_post.call_args[0][0]
        self.assertTrue(url.endswith("/pedido-validado"))


# ── notificar_stock_critico ────────────────────────────────────────────────────

class NotificarStockCriticoTest(TestCase):

    def setUp(self):
        self.prod = make_producto()

    @override_settings(N8N_WEBHOOK_BASE="http://n8n-test:5678/webhook")
    @patch("apps.integracion.webhooks.requests.post")
    def test_envia_payload_correcto(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        notificar_stock_critico(self.prod)
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["producto_id"], self.prod.pk)
        self.assertEqual(payload["nombre"], self.prod.nombre)
        self.assertIn("deficit", payload)

    @override_settings(N8N_WEBHOOK_BASE="http://n8n-test:5678/webhook")
    @patch("apps.integracion.webhooks.requests.post")
    def test_deficit_calculado_correctamente(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        # stock_actual=3, stock_minimo=3 → deficit=0
        notificar_stock_critico(self.prod)
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["deficit"], 0)

    @override_settings(N8N_WEBHOOK_BASE="http://n8n-test:5678/webhook")
    @patch("apps.integracion.webhooks.requests.post")
    def test_llama_a_ruta_stock_critico(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        notificar_stock_critico(self.prod)
        url = mock_post.call_args[0][0]
        self.assertTrue(url.endswith("/stock-critico"))
