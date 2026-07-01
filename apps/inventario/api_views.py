from django.db.models import Max, Min, Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Categoria, Producto
from .serializers import CategoriaSerializer, ProductoSerializer


class ProductoListAPIView(generics.ListAPIView):
    """
    GET /api/productos/
    Parámetros opcionales: categoria, marca, material, forma,
                           precio_min, precio_max, q (búsqueda de texto)
    Solo devuelve productos activos.
    """
    serializer_class = ProductoSerializer

    def get_queryset(self):
        qs = Producto.objects.filter(activo=True).select_related("categoria")
        p = self.request.query_params

        if cat := p.get("categoria"):
            qs = qs.filter(categoria_id=cat)
        if marcas := p.getlist("marca"):
            qs = qs.filter(marca__in=marcas)
        if materiales := p.getlist("material"):
            qs = qs.filter(material__in=materiales)
        if formas := p.getlist("forma"):
            qs = qs.filter(forma__in=formas)
        if precio_min := p.get("precio_min"):
            qs = qs.filter(precio__gte=precio_min)
        if precio_max := p.get("precio_max"):
            qs = qs.filter(precio__lte=precio_max)
        if q := p.get("q"):
            qs = qs.filter(Q(nombre__icontains=q) | Q(marca__icontains=q) | Q(descripcion__icontains=q))

        return qs


class ProductoDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductoSerializer
    queryset = Producto.objects.filter(activo=True).select_related("categoria")


class CategoriaListAPIView(generics.ListAPIView):
    serializer_class = CategoriaSerializer
    queryset = Categoria.objects.filter(productos__activo=True).distinct()


class FiltrosMetaAPIView(APIView):
    """
    GET /api/filtros/
    Devuelve las opciones disponibles para poblar la barra lateral de filtros.
    """
    def get(self, request):
        qs = Producto.objects.filter(activo=True)
        agg = qs.aggregate(precio_min=Min("precio"), precio_max=Max("precio"))
        # order_by() limpia el Meta.ordering del modelo; sin eso PostgreSQL
        # incluye las columnas de ordenamiento en la SELECT DISTINCT y devuelve
        # una fila por producto en lugar de valores únicos.
        def distinct_field(field):
            return qs.order_by(field).values_list(field, flat=True).distinct()

        return Response({
            "marcas": sorted(distinct_field("marca")),
            "materiales": sorted(v for v in distinct_field("material") if v),
            "formas": sorted(v for v in distinct_field("forma") if v),
            "precio_min": float(agg["precio_min"] or 0),
            "precio_max": float(agg["precio_max"] or 0),
        })
