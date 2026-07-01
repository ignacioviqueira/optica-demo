from django.templatetags.static import static
from rest_framework import serializers

from .models import Categoria, Producto


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["id", "nombre", "descripcion"]


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)
    imagen_url = serializers.SerializerMethodField()
    imagen_vto_url = serializers.SerializerMethodField()
    stock_critico = serializers.BooleanField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id", "nombre", "marca", "descripcion",
            "precio", "stock_actual", "stock_minimo", "stock_critico",
            "categoria", "categoria_nombre",
            "material", "forma", "color", "medidas", "caracteristicas",
            "imagen_url", "imagen_vto_url",
        ]

    def _static_abs(self, request, path: str):
        if path and request:
            return request.build_absolute_uri(static(path))
        return None

    def get_imagen_url(self, obj):
        return self._static_abs(self.context.get("request"), obj.imagen)

    def get_imagen_vto_url(self, obj):
        return self._static_abs(self.context.get("request"), obj.imagen_vto)
