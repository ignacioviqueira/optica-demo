from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    marca = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name="productos"
    )
    imagen = models.ImageField(upload_to="productos/", null=True, blank=True)
    material = models.CharField(max_length=100, blank=True)
    forma = models.CharField(max_length=100, blank=True)
    # Baja lógica: oculta del catálogo pero conserva el histórico (HU-02)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["categoria", "marca", "nombre"]

    def __str__(self):
        return f"{self.marca} — {self.nombre}"

    @property
    def stock_critico(self):
        return self.stock_actual <= self.stock_minimo

    def descontar_stock(self, cantidad: int) -> None:
        """Descuenta stock al confirmar una venta. Lanza ValueError si es insuficiente."""
        if self.stock_actual < cantidad:
            raise ValueError(
                f"Stock insuficiente para «{self}»: "
                f"{self.stock_actual} disponible(s), se requieren {cantidad}."
            )
        self.stock_actual = models.F("stock_actual") - cantidad
        self.save(update_fields=["stock_actual"])
        self.refresh_from_db(fields=["stock_actual"])
