from django.contrib import admin
from django.utils.html import format_html

from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion", "total_productos")
    search_fields = ("nombre",)

    @admin.display(description="Productos")
    def total_productos(self, obj):
        return obj.productos.count()


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "marca", "categoria", "material", "forma", "precio", "stock_actual", "stock_minimo", "estado_stock", "activo")
    list_filter = ("categoria", "marca", "material", "forma", "activo")
    search_fields = ("nombre", "marca")
    list_editable = ("stock_actual", "activo")

    @admin.display(description="Stock")
    def estado_stock(self, obj):
        if obj.stock_critico:
            return format_html('<span style="color:red;font-weight:bold;">⚠ {}/{}</span>', obj.stock_actual, obj.stock_minimo)
        return format_html('<span style="color:green;">OK {}/{}</span>', obj.stock_actual, obj.stock_minimo)
