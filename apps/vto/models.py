from django.conf import settings
from django.db import models


class EventoVTO(models.Model):
    """Conversión: usuario probó un armazón desde el VTO y lo añadió al carrito (HU-13)."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='eventos_vto',
    )
    producto = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.CASCADE,
        related_name='eventos_vto',
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Evento VTO'
        verbose_name_plural = 'Eventos VTO'

    def __str__(self):
        return f"{self.usuario} → {self.producto} ({self.timestamp:%Y-%m-%d %H:%M})"
