import math
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.inventario.models import Categoria, Producto

from .models import EventoVTO
from .vto_math import calcular_angulo_ocular, calcular_ancho_frame, calcular_ipd_px

User = get_user_model()


def make_user(email, rol, password='Test@1234'):
    return User.objects.create_user(
        email=email,
        username=email.split('@')[0],
        password=password,
        rol=rol,
    )


def make_producto(cat, nombre='Armazón VTO', precio='25000'):
    return Producto.objects.create(
        nombre=nombre,
        marca='MarcaVTO',
        precio=Decimal(precio),
        stock_actual=10,
        stock_minimo=2,
        categoria=cat,
    )


# ── Matemática de escala (HU-06/07) ──────────────────────────────────────────

class EscalaVTOTest(TestCase):
    """
    Verifica la función calcular_ancho_frame:
    el overlay debe escalar proporcionalmente al IPD medido en píxeles.
    """

    def test_ipd_igual_referencia_devuelve_ancho_frame_nominal(self):
        # 63 px IPD con ratio 140/63 → exactamente 140 px de ancho de frame
        resultado = calcular_ancho_frame(63.0, frame_mm=140.0, ipd_mm=63.0)
        self.assertAlmostEqual(resultado, 140.0, places=5)

    def test_escala_lineal_proporcional_al_ipd(self):
        ancho_60 = calcular_ancho_frame(60.0)
        ancho_120 = calcular_ancho_frame(120.0)
        self.assertAlmostEqual(ancho_120, ancho_60 * 2, places=5)

    def test_ipd_mayor_produce_frame_mas_ancho(self):
        self.assertGreater(calcular_ancho_frame(90), calcular_ancho_frame(70))

    def test_ipd_cero_lanza_valor_error(self):
        with self.assertRaises(ValueError):
            calcular_ancho_frame(0.0)

    def test_ipd_negativo_lanza_valor_error(self):
        with self.assertRaises(ValueError):
            calcular_ancho_frame(-10.0)

    def test_frame_personalizado_escala_correctamente(self):
        # Frame de 120 mm con IPD de referencia 60 mm
        resultado = calcular_ancho_frame(60.0, frame_mm=120.0, ipd_mm=60.0)
        self.assertAlmostEqual(resultado, 120.0, places=5)


# ── Matemática de rotación (HU-07) ───────────────────────────────────────────

class AnguloOcularVTOTest(TestCase):
    """
    Verifica la función calcular_angulo_ocular:
    el canvas debe rotarse según la inclinación del eje inter-pupilar.
    """

    def test_ojos_perfectamente_horizontales_angulo_cero(self):
        angulo = calcular_angulo_ocular(100, 200, 200, 200)
        self.assertAlmostEqual(angulo, 0.0, places=9)

    def test_ojo_derecho_mas_bajo_angulo_positivo(self):
        # right_y > left_y → eje inclinado hacia abajo a la derecha
        angulo = calcular_angulo_ocular(0, 0, 100, 50)
        self.assertGreater(angulo, 0)

    def test_ojo_derecho_mas_alto_angulo_negativo(self):
        angulo = calcular_angulo_ocular(0, 100, 100, 50)
        self.assertLess(angulo, 0)

    def test_inclinacion_45_grados_exacta(self):
        angulo = calcular_angulo_ocular(0, 0, 100, 100)
        self.assertAlmostEqual(angulo, math.pi / 4, places=9)

    def test_inclinacion_menos_45_grados(self):
        angulo = calcular_angulo_ocular(0, 100, 100, 0)
        self.assertAlmostEqual(angulo, -math.pi / 4, places=9)

    def test_angulo_en_rango_correcto(self):
        angulo = calcular_angulo_ocular(50, 120, 180, 110)
        self.assertGreaterEqual(angulo, -math.pi)
        self.assertLessEqual(angulo, math.pi)


# ── IPD en píxeles ────────────────────────────────────────────────────────────

class IPDCalculoTest(TestCase):
    def test_ojos_separados_100px_horizontalmente(self):
        ipd = calcular_ipd_px(0, 0, 100, 0)
        self.assertAlmostEqual(ipd, 100.0, places=5)

    def test_triangulo_pitagoras_3_4_5(self):
        ipd = calcular_ipd_px(0, 0, 30, 40)
        self.assertAlmostEqual(ipd, 50.0, places=5)

    def test_ipd_simetrico(self):
        ipd1 = calcular_ipd_px(0, 0, 80, 0)
        ipd2 = calcular_ipd_px(80, 0, 0, 0)
        self.assertAlmostEqual(ipd1, ipd2, places=9)


# ── Modelo EventoVTO (HU-13) ──────────────────────────────────────────────────

class EventoVTOModelTest(TestCase):
    def setUp(self):
        self.cat     = Categoria.objects.create(nombre='Armazones')
        self.user    = make_user('vto@test.com', 'cliente')
        self.prod    = make_producto(self.cat)

    def test_creacion_evento(self):
        ev = EventoVTO.objects.create(usuario=self.user, producto=self.prod)
        self.assertIsNotNone(ev.pk)
        self.assertIsNotNone(ev.timestamp)

    def test_str_contiene_usuario_y_producto(self):
        ev = EventoVTO.objects.create(usuario=self.user, producto=self.prod)
        self.assertIn(str(self.user), str(ev))

    def test_ordenamiento_por_timestamp_desc(self):
        ev1 = EventoVTO.objects.create(usuario=self.user, producto=self.prod)
        ev2 = EventoVTO.objects.create(usuario=self.user, producto=self.prod)
        eventos = list(EventoVTO.objects.all())
        self.assertEqual(eventos[0].pk, ev2.pk)


# ── API POST /api/vto/evento/ (HU-13) ─────────────────────────────────────────

class EventoVTOAPITest(TestCase):
    def setUp(self):
        self.cat     = Categoria.objects.create(nombre='Armazones')
        self.cliente = make_user('cliente_vto@test.com', 'cliente')
        self.ventas  = make_user('ventas_vto@test.com', 'ventas')
        self.prod    = make_producto(self.cat)
        self.client  = Client()

    def _post(self, user, data):
        self.client.force_login(user)
        return self.client.post(
            '/api/vto/evento/',
            data,
            content_type='application/json',
        )

    def test_crea_evento_correctamente(self):
        r = self._post(self.cliente, {'producto_id': self.prod.pk})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(EventoVTO.objects.count(), 1)
        ev = EventoVTO.objects.first()
        self.assertEqual(ev.producto_id, self.prod.pk)
        self.assertEqual(ev.usuario_id, self.cliente.pk)

    def test_respuesta_incluye_id_y_timestamp(self):
        r = self._post(self.cliente, {'producto_id': self.prod.pk})
        data = r.json()
        self.assertIn('id', data)
        self.assertIn('timestamp', data)

    def test_sin_producto_id_devuelve_400(self):
        r = self._post(self.cliente, {})
        self.assertEqual(r.status_code, 400)

    def test_producto_inexistente_devuelve_404(self):
        r = self._post(self.cliente, {'producto_id': 99999})
        self.assertEqual(r.status_code, 404)

    def test_no_autenticado_devuelve_403(self):
        r = self.client.post(
            '/api/vto/evento/',
            {'producto_id': self.prod.pk},
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 403)

    def test_producto_inactivo_devuelve_404(self):
        self.prod.activo = False
        self.prod.save()
        r = self._post(self.cliente, {'producto_id': self.prod.pk})
        self.assertEqual(r.status_code, 404)

    def test_rol_ventas_no_puede_registrar_evento(self):
        r = self._post(self.ventas, {'producto_id': self.prod.pk})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(EventoVTO.objects.count(), 0)


# ── Vista HTML /vto/ ──────────────────────────────────────────────────────────

class VTOViewTest(TestCase):
    def setUp(self):
        self.cat     = Categoria.objects.create(nombre='Armazones')
        self.cliente = make_user('c_vto@test.com', 'cliente')
        self.prod    = make_producto(self.cat)
        self.client  = Client()

    def test_vto_accesible_para_cliente(self):
        self.client.force_login(self.cliente)
        r = self.client.get(reverse('vto:index'))
        self.assertEqual(r.status_code, 200)

    def test_vto_con_producto_carga_correctamente(self):
        self.client.force_login(self.cliente)
        r = self.client.get(reverse('vto:index') + f'?producto={self.prod.pk}')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.prod.nombre)

    def test_vto_sin_autenticacion_redirige(self):
        r = self.client.get(reverse('vto:index'))
        self.assertEqual(r.status_code, 302)

    def test_vto_producto_inexistente_devuelve_404(self):
        self.client.force_login(self.cliente)
        r = self.client.get(reverse('vto:index') + '?producto=99999')
        self.assertEqual(r.status_code, 404)

    def test_vto_usa_imagen_vto_para_overlay(self):
        """Con imagen_vto seteada el context incluye producto_frame_url."""
        self.prod.imagen_vto = "productos/rayban_clubmaster_vto.png"
        self.prod.save()
        self.client.force_login(self.cliente)
        r = self.client.get(reverse('vto:index') + f'?producto={self.prod.pk}')
        self.assertEqual(r.status_code, 200)
        # La URL del frame debe contener el nombre del archivo VTO
        frame_url = r.context.get('producto_frame_url')
        self.assertIsNotNone(frame_url)
        self.assertIn("rayban_clubmaster_vto", frame_url)

    def test_vto_sin_imagen_vto_no_setea_frame_url(self):
        """Sin imagen_vto no se pasa producto_frame_url al template."""
        self.prod.imagen_vto = ""
        self.prod.save()
        self.client.force_login(self.cliente)
        r = self.client.get(reverse('vto:index') + f'?producto={self.prod.pk}')
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.context.get('producto_frame_url'))

    def test_vto_pasa_armazones_al_context(self):
        """El context incluye todos los armazones activos para el panel de thumbnails."""
        self.client.force_login(self.cliente)
        r = self.client.get(reverse('vto:index'))
        self.assertEqual(r.status_code, 200)
        armazones = r.context.get('armazones')
        self.assertIsNotNone(armazones)
        # El armazón creado en setUp está en Armazones y activo
        ids = [a.id for a in armazones]
        self.assertIn(self.prod.pk, ids)

    def test_vto_armazones_excluye_inactivos(self):
        """Un armazón inactivo no aparece en el panel de thumbnails."""
        self.prod.activo = False
        self.prod.save()
        self.client.force_login(self.cliente)
        r = self.client.get(reverse('vto:index'))
        ids = [a.id for a in r.context['armazones']]
        self.assertNotIn(self.prod.pk, ids)

    def test_vto_armazones_solo_incluye_categoria_armazones(self):
        """Cristales y lentes de contacto no aparecen en el panel de armazones."""
        from apps.inventario.models import Categoria as Cat
        cat_cristales = Cat.objects.create(nombre='Cristales')
        cristal = make_producto(cat_cristales, nombre='Varilux VTO')
        self.client.force_login(self.cliente)
        r = self.client.get(reverse('vto:index'))
        ids = [a.id for a in r.context['armazones']]
        self.assertNotIn(cristal.pk, ids)
