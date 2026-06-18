from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.inventario.models import Producto


class Receta(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recetas",
    )
    esfera_od = models.DecimalField(max_digits=5, decimal_places=2)
    cilindro_od = models.DecimalField(max_digits=5, decimal_places=2)
    eje_od = models.PositiveSmallIntegerField()
    dnp = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_emision = models.DateField()

    class Meta:
        verbose_name = "Receta"
        verbose_name_plural = "Recetas"
        ordering = ["-fecha_emision"]

    def __str__(self):
        return f"Receta #{self.pk} — {self.usuario} ({self.fecha_emision})"


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE_VALIDACION = "pendiente_validacion", "Confirmado - Pendiente de Validación"
        EN_PROCESO = "en_proceso", "En Proceso de Armado"
        LISTO = "listo", "Listo para Entrega"
        RECHAZADO = "rechazado", "Rechazado"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pedidos",
    )
    fecha = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(
        max_length=25,
        choices=Estado.choices,
        default=Estado.PENDIENTE_VALIDACION,
    )
    receta = models.ForeignKey(
        Receta,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pedidos",
    )
    receta_imagen = models.ImageField(
        upload_to="recetas/",
        null=True,
        blank=True,
        verbose_name="Imagen de receta",
    )
    motivo_rechazo = models.TextField(blank=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Pedido #{self.pk} — {self.usuario} [{self.get_estado_display()}]"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="detalles"
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name="detalles"
    )
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedido"

    def __str__(self):
        return f"{self.cantidad}× {self.producto} @ ${self.precio_unitario}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
