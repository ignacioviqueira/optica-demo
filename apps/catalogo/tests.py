from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.inventario.models import Categoria, Producto

User = get_user_model()


def make_user(email, rol, password="Test@1234"):
    return User.objects.create_user(
        email=email,
        username=email.split("@")[0],
        password=password,
        rol=rol,
    )


# ── Fix 1: la API de categorías devuelve formato paginado ─────────────────────

class CategoriaAPIPaginadaTest(TestCase):
    def setUp(self):
        self.cliente = make_user("cat_cliente@test.com", "cliente")
        self.client  = Client()
        self.client.force_login(self.cliente)

    def test_categorias_api_devuelve_estructura_paginada(self):
        """La API usa PageNumberPagination; el JS debe leer .results, no el objeto raíz."""
        r = self.client.get("/api/categorias/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("results", data)
        self.assertIn("count", data)

    def test_categorias_api_results_es_lista(self):
        r = self.client.get("/api/categorias/")
        data = r.json()
        self.assertIsInstance(data["results"], list)


# ── Fix 2: USER_ROL se renderiza correctamente por rol ───────────────────────

class CatalogoRolScriptTest(TestCase):
    def setUp(self):
        self.cliente  = make_user("rol_cliente@test.com", "cliente")
        self.ventas   = make_user("rol_ventas@test.com", "ventas")
        self.gerencia = make_user("rol_gerencia@test.com", "gerencia")
        self.client   = Client()

    def _get_catalogo(self, user):
        self.client.force_login(user)
        return self.client.get(reverse("catalogo:index"))

    def test_user_rol_cliente_en_script(self):
        r = self._get_catalogo(self.cliente)
        self.assertContains(r, 'USER_ROL')
        self.assertContains(r, '"cliente"')

    def test_user_rol_ventas_en_script(self):
        r = self._get_catalogo(self.ventas)
        self.assertContains(r, 'USER_ROL')
        self.assertContains(r, '"ventas"')

    def test_user_rol_gerencia_en_script(self):
        r = self._get_catalogo(self.gerencia)
        self.assertContains(r, 'USER_ROL')
        self.assertContains(r, '"gerencia"')


# ── Vista detalle /catalogo/<pk>/ ─────────────────────────────────────────────

class DetalleViewTest(TestCase):
    def setUp(self):
        self.cat_arm = Categoria.objects.create(nombre="Armazones")
        self.cat_cri = Categoria.objects.create(nombre="Cristales")
        self.cliente = make_user("det_cli@test.com", "cliente")
        self.client  = Client()
        self.client.force_login(self.cliente)

        self.armazon = Producto.objects.create(
            nombre="Clubmaster", marca="Ray-Ban",
            precio=Decimal("142000"), stock_actual=8, stock_minimo=3,
            categoria=self.cat_arm,
        )
        self.cristal = Producto.objects.create(
            nombre="Varilux", marca="Essilor",
            precio=Decimal("65000"), stock_actual=10, stock_minimo=5,
            categoria=self.cat_cri,
        )

    def test_detalle_armazon_incluye_boton_vto(self):
        r = self.client.get(reverse("catalogo:detalle", args=[self.armazon.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["es_armazon"])
        self.assertContains(r, "Prueba Virtual")

    def test_detalle_cristal_no_incluye_boton_vto(self):
        r = self.client.get(reverse("catalogo:detalle", args=[self.cristal.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.context["es_armazon"])
        self.assertNotContains(r, "Prueba Virtual")

    def test_detalle_404_para_producto_inactivo(self):
        self.armazon.activo = False
        self.armazon.save()
        r = self.client.get(reverse("catalogo:detalle", args=[self.armazon.pk]))
        self.assertEqual(r.status_code, 404)


# ── API /api/filtros/ — sin duplicados (DISTINCT) ────────────────────────────

class FiltrosDISTINCTTest(TestCase):
    """
    Verifica que /api/filtros/ devuelve cada valor exactamente una vez,
    incluso cuando hay múltiples productos con el mismo material/forma/marca.
    El Meta.ordering del modelo Producto rompía DISTINCT en PostgreSQL si no
    se limpia antes de la consulta.
    """
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Armazones")
        self.cliente = make_user("filt@test.com", "cliente")
        self.client  = Client()
        self.client.force_login(self.cliente)

        for i in range(3):
            Producto.objects.create(
                nombre=f"Armazón {i}", marca="Ray-Ban",
                precio=Decimal("50000"), stock_actual=5, stock_minimo=2,
                categoria=self.cat,
                material="O-Matter", forma="Cuadrado",
            )

    def test_marcas_sin_duplicados(self):
        r = self.client.get("/api/filtros/")
        self.assertEqual(r.status_code, 200)
        marcas = r.json()["marcas"]
        self.assertEqual(len(marcas), len(set(marcas)))

    def test_materiales_sin_duplicados(self):
        r = self.client.get("/api/filtros/")
        materiales = r.json()["materiales"]
        self.assertEqual(len(materiales), len(set(materiales)))

    def test_formas_sin_duplicados(self):
        r = self.client.get("/api/filtros/")
        formas = r.json()["formas"]
        self.assertEqual(len(formas), len(set(formas)))
