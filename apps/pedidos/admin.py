from django.contrib import admin

from .models import DetallePedido, Pedido, Receta


@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "esfera_od", "cilindro_od", "eje_od", "dnp", "fecha_emision")
    list_filter = ("fecha_emision",)
    search_fields = ("usuario__email", "usuario__first_name")
    date_hierarchy = "fecha_emision"


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ("subtotal",)

    @admin.display(description="Subtotal")
    def subtotal(self, obj):
        return f"${obj.subtotal:,.2f}"


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "fecha", "total", "estado", "receta")
    list_filter = ("estado",)
    search_fields = ("usuario__email",)
    readonly_fields = ("fecha",)
    inlines = [DetallePedidoInline]
    date_hierarchy = "fecha"
