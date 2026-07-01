from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Categoria, Producto, ProductoImagen

User = get_user_model()


def make_user(email, rol, password="Test@1234"):
    return User.objects.create_user(
        email=email,
        username=email.split("@")[0],
        password=password,
        rol=rol,
    )


def make_producto(cat, nombre="Armazón Test", marca="MarcaA",
                  precio="20000", stock_actual=10, stock_minimo=3,
                  material="Acetato", forma="Cuadrado"):
    return Producto.objects.create(
        nombre=nombre,
        marca=marca,
        precio=Decimal(precio),
        stock_actual=stock_actual,
        stock_minimo=stock_minimo,
        categoria=cat,
        material=material,
        forma=forma,
    )


# ── Modelo ────────────────────────────────────────────────────────────────────

class CategoriaTest(TestCase):
    def test_str(self):
        cat = Categoria.objects.create(nombre="Armazones")
        self.assertEqual(str(cat), "Armazones")


class ProductoModelTest(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Armazones")

    def _make(self, stock_actual, stock_minimo):
        return make_producto(self.cat, stock_actual=stock_actual, stock_minimo=stock_minimo)

    def test_stock_critico_cuando_igual_al_minimo(self):
        self.assertTrue(self._make(3, 3).stock_critico)

    def test_stock_critico_cuando_menor_al_minimo(self):
        self.assertTrue(self._make(1, 3).stock_critico)

    def test_stock_no_critico_cuando_mayor_al_minimo(self):
        self.assertFalse(self._make(10, 3).stock_critico)

    def test_str_incluye_marca_y_nombre(self):
        p = self._make(5, 3)
        self.assertIn("MarcaA", str(p))
        self.assertIn("Armazón Test", str(p))

    def test_activo_por_defecto(self):
        p = self._make(5, 3)
        self.assertTrue(p.activo)

    def test_descontar_stock_reduce_stock(self):
        p = self._make(10, 3)
        p.descontar_stock(3)
        self.assertEqual(p.stock_actual, 7)

    def test_descontar_stock_insuficiente_lanza_error(self):
        p = self._make(2, 3)
        with self.assertRaises(ValueError):
            p.descontar_stock(5)

    def test_descontar_stock_exactamente_disponible(self):
        p = self._make(5, 3)
        p.descontar_stock(5)
        self.assertEqual(p.stock_actual, 0)


# ── API REST ──────────────────────────────────────────────────────────────────

class APIProductoTest(TestCase):
    def setUp(self):
        self.cat1 = Categoria.objects.create(nombre="Armazones")
        self.cat2 = Categoria.objects.create(nombre="Cristales")
        self.user = make_user("cliente@test.com", "cliente")
        self.client = Client()
        self.client.force_login(self.user)

        self.p1 = make_producto(self.cat1, nombre="Wayfarer", marca="Ray-Ban",
                                precio="45000", material="Acetato", forma="Cuadrado")
        self.p2 = make_producto(self.cat1, nombre="Holbrook", marca="Oakley",
                                precio="38000", material="Acetato", forma="Cuadrado")
        self.p3 = make_producto(self.cat2, nombre="Varilux", marca="Essilor",
                                precio="65000", material="Orgánico", forma="Progresivo")
        # producto inactivo — nunca debe aparecer en la API
        self.p_inactivo = make_producto(self.cat1, nombre="Oculto", marca="X")
        self.p_inactivo.activo = False
        self.p_inactivo.save()

    def get(self, url):
        return self.client.get(url)

    def test_lista_devuelve_solo_activos(self):
        r = self.get("/api/productos/")
        self.assertEqual(r.status_code, 200)
        nombres = [p["nombre"] for p in r.json()["results"]]
        self.assertNotIn("Oculto", nombres)
        self.assertIn("Wayfarer", nombres)

    def test_filtro_por_categoria(self):
        r = self.get(f"/api/productos/?categoria={self.cat2.pk}")
        nombres = [p["nombre"] for p in r.json()["results"]]
        self.assertIn("Varilux", nombres)
        self.assertNotIn("Wayfarer", nombres)

    def test_filtro_por_marca(self):
        r = self.get("/api/productos/?marca=Ray-Ban")
        nombres = [p["nombre"] for p in r.json()["results"]]
        self.assertEqual(nombres, ["Wayfarer"])

    def test_filtro_por_multiples_marcas(self):
        r = self.get("/api/productos/?marca=Ray-Ban&marca=Oakley")
        nombres = set(p["nombre"] for p in r.json()["results"])
        self.assertIn("Wayfarer", nombres)
        self.assertIn("Holbrook", nombres)
        self.assertNotIn("Varilux", nombres)

    def test_filtro_precio_min(self):
        r = self.get("/api/productos/?precio_min=60000")
        nombres = [p["nombre"] for p in r.json()["results"]]
        self.assertIn("Varilux", nombres)
        self.assertNotIn("Wayfarer", nombres)

    def test_filtro_precio_max(self):
        r = self.get("/api/productos/?precio_max=40000")
        nombres = [p["nombre"] for p in r.json()["results"]]
        self.assertIn("Holbrook", nombres)
        self.assertNotIn("Varilux", nombres)

    def test_busqueda_texto(self):
        r = self.get("/api/productos/?q=way")
        nombres = [p["nombre"] for p in r.json()["results"]]
        self.assertIn("Wayfarer", nombres)
        self.assertNotIn("Holbrook", nombres)

    def test_no_autenticado_devuelve_403(self):
        c = Client()
        r = c.get("/api/productos/")
        self.assertEqual(r.status_code, 403)

    def test_filtros_meta_devuelve_marcas(self):
        r = self.get("/api/filtros/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("Ray-Ban", data["marcas"])
        self.assertIn("marcas", data)
        self.assertIn("materiales", data)
        self.assertIn("formas", data)

    def test_categorias_devuelve_todas(self):
        r = self.get("/api/categorias/")
        data = r.json()
        items = data.get("results", data)  # handle paginated or plain list
        nombres = [c["nombre"] for c in items]
        self.assertIn("Armazones", nombres)
        self.assertIn("Cristales", nombres)


# ── CRUD HTML (vistas para Gerencia) ─────────────────────────────────────────

class InventarioCRUDTest(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Armazones")
        self.gerencia = make_user("g@test.com", "gerencia")
        self.cliente  = make_user("c@test.com", "cliente")
        self.client   = Client()

    def _login(self, user):
        self.client.force_login(user)

    def test_lista_requiere_autenticacion(self):
        r = self.client.get(reverse("inventario:lista"))
        self.assertEqual(r.status_code, 302)

    def test_lista_requiere_rol_gerencia(self):
        self._login(self.cliente)
        r = self.client.get(reverse("inventario:lista"))
        self.assertEqual(r.status_code, 403)

    def test_gerencia_puede_ver_lista(self):
        self._login(self.gerencia)
        r = self.client.get(reverse("inventario:lista"))
        self.assertEqual(r.status_code, 200)

    def test_gerencia_puede_crear_producto(self):
        self._login(self.gerencia)
        r = self.client.post(reverse("inventario:nuevo"), {
            "nombre": "Nuevo Armazón",
            "marca": "MarcaNueva",
            "precio": "15000",
            "stock_actual": 10,
            "stock_minimo": 3,
            "categoria": self.cat.pk,
            "material": "Metal",
            "forma": "Redondo",
        })
        self.assertTrue(Producto.objects.filter(nombre="Nuevo Armazón").exists())

    def test_gerencia_puede_hacer_baja_logica(self):
        p = make_producto(self.cat)
        self._login(self.gerencia)
        self.client.post(reverse("inventario:toggle", args=[p.pk]))
        p.refresh_from_db()
        self.assertFalse(p.activo)

    def test_toggle_reactiva_producto_inactivo(self):
        p = make_producto(self.cat)
        p.activo = False
        p.save()
        self._login(self.gerencia)
        self.client.post(reverse("inventario:toggle", args=[p.pk]))
        p.refresh_from_db()
        self.assertTrue(p.activo)

    def test_cliente_no_puede_crear_producto(self):
        self._login(self.cliente)
        r = self.client.post(reverse("inventario:nuevo"), {
            "nombre": "Hack",
            "marca": "X",
            "precio": "1",
            "stock_actual": 1,
            "stock_minimo": 1,
            "categoria": self.cat.pk,
        })
        self.assertEqual(r.status_code, 403)


# ── ProductoImagen ────────────────────────────────────────────────────────────

class ProductoImagenTest(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Armazones")
        self.prod = make_producto(
            self.cat,
            nombre="Clubmaster Optics",
            marca="Ray-Ban",
        )
        self.prod.imagen = "productos/rayban_clubmaster_1.png"
        self.prod.imagen_vto = "productos/rayban_clubmaster_vto.png"
        self.prod.save()

    def test_str_incluye_producto_y_orden(self):
        img = ProductoImagen.objects.create(
            producto=self.prod,
            imagen="productos/rayban_clubmaster_2.png",
            orden=1,
        )
        self.assertIn(str(self.prod), str(img))
        self.assertIn("1", str(img))

    def test_ordenacion_por_campo_orden(self):
        ProductoImagen.objects.create(producto=self.prod, imagen="x_3.png", orden=2)
        ProductoImagen.objects.create(producto=self.prod, imagen="x_2.png", orden=1)
        paths = list(self.prod.imagenes.values_list("imagen", flat=True))
        self.assertEqual(paths, ["x_2.png", "x_3.png"])

    def test_cascade_delete_con_producto(self):
        ProductoImagen.objects.create(producto=self.prod, imagen="x_2.png", orden=1)
        self.prod.delete()
        self.assertEqual(ProductoImagen.objects.count(), 0)

    def test_imagen_vto_campo_en_modelo(self):
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.imagen_vto, "productos/rayban_clubmaster_vto.png")

    def test_serializer_expone_imagen_vto_url(self):
        from django.test import RequestFactory
        from .serializers import ProductoSerializer
        request = RequestFactory().get("/")
        request.user = make_user("x@x.com", "cliente")
        data = ProductoSerializer(self.prod, context={"request": request}).data
        self.assertIn("imagen_vto_url", data)
        # imagen_vto está seteada → la URL no debe ser None
        self.assertIsNotNone(data["imagen_vto_url"])
        self.assertIn("rayban_clubmaster_vto", data["imagen_vto_url"])
