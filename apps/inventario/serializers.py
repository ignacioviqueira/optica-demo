from rest_framework import serializers

from .models import Categoria, Producto


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["id", "nombre", "descripcion"]


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)
    imagen_url = serializers.SerializerMethodField()
    stock_critico = serializers.BooleanField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id", "nombre", "marca", "descripcion",
            "precio", "stock_actual", "stock_minimo", "stock_critico",
            "categoria", "categoria_nombre",
            "material", "forma",
            "imagen_url",
        ]

    def get_imagen_url(self, obj):
        request = self.context.get("request")
        if obj.imagen and request:
            return request.build_absolute_uri(obj.imagen.url)
        return None
