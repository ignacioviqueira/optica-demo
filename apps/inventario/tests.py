from decimal import Decimal

from django.test import TestCase

from .models import Categoria, Producto


class CategoriaTest(TestCase):
    def test_str(self):
        cat = Categoria.objects.create(nombre="Armazones")
        self.assertEqual(str(cat), "Armazones")


class ProductoTest(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Armazones")

    def _make_producto(self, stock_actual, stock_minimo):
        return Producto.objects.create(
            nombre="Test Frame",
            marca="TestMarca",
            precio=Decimal("10000.00"),
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            categoria=self.cat,
        )

    def test_stock_critico_cuando_igual_al_minimo(self):
        p = self._make_producto(stock_actual=3, stock_minimo=3)
        self.assertTrue(p.stock_critico)

    def test_stock_critico_cuando_menor_al_minimo(self):
        p = self._make_producto(stock_actual=1, stock_minimo=3)
        self.assertTrue(p.stock_critico)

    def test_stock_no_critico_cuando_mayor_al_minimo(self):
        p = self._make_producto(stock_actual=10, stock_minimo=3)
        self.assertFalse(p.stock_critico)

    def test_str_incluye_marca_y_nombre(self):
        p = self._make_producto(stock_actual=5, stock_minimo=3)
        self.assertIn("TestMarca", str(p))
        self.assertIn("Test Frame", str(p))
