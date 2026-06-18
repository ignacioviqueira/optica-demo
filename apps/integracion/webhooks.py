"""
Capa de integración — llamadas salientes a los webhooks de n8n (HU-integración).

Todas las funciones son fire-and-forget: si n8n no responde o no está
configurado, el error se registra pero nunca bloquea el flujo principal de Django.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 3  # segundos; n8n local responde en <100 ms normalmente


def _post_webhook(path: str, payload: dict) -> None:
    """Envía un POST al webhook de n8n indicado. Falla silenciosamente."""
    base = getattr(settings, "N8N_WEBHOOK_BASE", "").rstrip("/")
    if not base:
        logger.debug("[n8n] N8N_WEBHOOK_BASE vacío — webhook '%s' omitido.", path)
        return
    url = f"{base}/{path}"
    try:
        resp = requests.post(url, json=payload, timeout=_TIMEOUT)
        resp.raise_for_status()
        logger.info("[n8n] %s → %s", path, resp.status_code)
    except requests.exceptions.ConnectionError:
        logger.warning("[n8n] '%s' — n8n no disponible (ConnectionError).", path)
    except requests.exceptions.Timeout:
        logger.warning("[n8n] '%s' — timeout después de %ss.", path, _TIMEOUT)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[n8n] '%s' — error inesperado: %s", path, exc)


def notificar_pedido_validado(pedido) -> None:
    """Dispara el flujo 'pedido-validado' cuando Ventas/Gerencia aprueba un pedido."""
    _post_webhook("pedido-validado", {
        "pedido_id": pedido.pk,
        "usuario_email": pedido.usuario.email,
        "usuario_nombre": pedido.usuario.get_full_name() or pedido.usuario.email,
        "total": str(pedido.total),
        "estado": pedido.get_estado_display(),
    })


def notificar_stock_critico(producto) -> None:
    """Dispara el flujo 'stock-critico' cuando el stock de un producto cae al mínimo."""
    _post_webhook("stock-critico", {
        "producto_id": producto.pk,
        "nombre": producto.nombre,
        "marca": producto.marca,
        "stock_actual": producto.stock_actual,
        "stock_minimo": producto.stock_minimo,
        "deficit": max(0, producto.stock_minimo - producto.stock_actual),
    })
