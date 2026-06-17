from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

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
