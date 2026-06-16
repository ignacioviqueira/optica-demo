from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .validators import StrongPasswordValidator

User = get_user_model()

LOGIN_URL = "/cuentas/login/"


def make_user(email, rol=User.Rol.CLIENTE, password="Test@1234"):
    return User.objects.create_user(
        email=email,
        username=email.split("@")[0],
        password=password,
        rol=rol,
    )


# ── Modelo ────────────────────────────────────────────────────────────────────

class CustomUserTest(TestCase):
    def test_email_es_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_rol_default_es_cliente(self):
        user = make_user("def@test.com")
        self.assertEqual(user.rol, User.Rol.CLIENTE)

    def test_str_devuelve_email(self):
        user = make_user("str@test.com")
        self.assertEqual(str(user), "str@test.com")

    def test_is_locked_false_cuando_sin_bloqueo(self):
        user = make_user("lock0@test.com")
        self.assertFalse(user.is_locked)

    def test_is_locked_true_cuando_locked_until_en_futuro(self):
        user = make_user("lock1@test.com")
        user.locked_until = timezone.now() + timedelta(minutes=10)
        user.save()
        self.assertTrue(user.is_locked)

    def test_is_locked_false_cuando_locked_until_en_pasado(self):
        user = make_user("lock2@test.com")
        user.locked_until = timezone.now() - timedelta(minutes=1)
        user.save()
        self.assertFalse(user.is_locked)


# ── Validador de contraseña ───────────────────────────────────────────────────

class StrongPasswordValidatorTest(TestCase):
    v = StrongPasswordValidator()

    def _assertInvalid(self, pwd):
        with self.assertRaises(ValidationError):
            self.v.validate(pwd)

    def test_acepta_contrasena_valida(self):
        self.v.validate("Valida@123")  # no debe lanzar

    def test_rechaza_sin_mayuscula(self):
        self._assertInvalid("minuscula@1")

    def test_rechaza_sin_minuscula(self):
        self._assertInvalid("MAYUSCULA@1")

    def test_rechaza_sin_numero(self):
        self._assertInvalid("SinNumero@!")

    def test_rechaza_sin_especial(self):
        self._assertInvalid("SinEspecial1")

    def test_get_help_text_no_vacio(self):
        self.assertTrue(len(self.v.get_help_text()) > 0)


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user("cliente@test.com", User.Rol.CLIENTE)

    def test_get_muestra_formulario(self):
        r = self.client.get(LOGIN_URL)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Correo electrónico")

    def test_login_exitoso_redirige(self):
        r = self.client.post(LOGIN_URL, {"email": "cliente@test.com", "password": "Test@1234"})
        self.assertEqual(r.status_code, 302)

    def test_login_redirige_a_catalogo_para_cliente(self):
        r = self.client.post(LOGIN_URL, {"email": "cliente@test.com", "password": "Test@1234"}, follow=True)
        self.assertRedirects(r, "/catalogo/")

    def test_login_redirige_a_dashboard_para_gerencia(self):
        make_user("gerencia@test.com", User.Rol.GERENCIA)
        r = self.client.post(LOGIN_URL, {"email": "gerencia@test.com", "password": "Test@1234"}, follow=True)
        self.assertRedirects(r, "/dashboard/")

    def test_login_redirige_a_operativo_para_ventas(self):
        make_user("ventas@test.com", User.Rol.VENTAS)
        r = self.client.post(LOGIN_URL, {"email": "ventas@test.com", "password": "Test@1234"}, follow=True)
        self.assertRedirects(r, "/pedidos/operativo/")

    def test_credenciales_incorrectas_muestra_error(self):
        r = self.client.post(LOGIN_URL, {"email": "cliente@test.com", "password": "Mala@1234"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "incorrectos")

    def test_email_inexistente_muestra_error(self):
        r = self.client.post(LOGIN_URL, {"email": "noexiste@test.com", "password": "Test@1234"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "incorrectos")

    def test_intento_fallido_incrementa_contador(self):
        self.client.post(LOGIN_URL, {"email": "cliente@test.com", "password": "Mala@1234"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 1)

    def test_cinco_intentos_bloquean_cuenta(self):
        for _ in range(5):
            self.client.post(LOGIN_URL, {"email": "cliente@test.com", "password": "Mala@1234"})
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked)

    def test_cuenta_bloqueada_rechaza_credenciales_correctas(self):
        self.user.locked_until = timezone.now() + timedelta(minutes=10)
        self.user.failed_login_attempts = 5
        self.user.save()
        r = self.client.post(LOGIN_URL, {"email": "cliente@test.com", "password": "Test@1234"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "bloqueada")

    def test_usuario_ya_autenticado_redirige(self):
        self.client.force_login(self.user)
        r = self.client.get(LOGIN_URL)
        self.assertEqual(r.status_code, 302)


# ── Registro ──────────────────────────────────────────────────────────────────

class RegistroViewTest(TestCase):
    REGISTRO_URL = "/cuentas/registro/"
    DATOS_VALIDOS = {
        "email": "nuevo@test.com",
        "first_name": "Ana",
        "last_name": "Pérez",
        "password1": "Nuevo@1234",
        "password2": "Nuevo@1234",
    }

    def test_get_muestra_formulario(self):
        r = self.client.get(self.REGISTRO_URL)
        self.assertEqual(r.status_code, 200)

    def test_registro_exitoso_crea_usuario(self):
        self.client.post(self.REGISTRO_URL, self.DATOS_VALIDOS)
        self.assertTrue(User.objects.filter(email="nuevo@test.com").exists())

    def test_registro_asigna_rol_cliente(self):
        self.client.post(self.REGISTRO_URL, self.DATOS_VALIDOS)
        user = User.objects.get(email="nuevo@test.com")
        self.assertEqual(user.rol, User.Rol.CLIENTE)

    def test_registro_exitoso_redirige_al_catalogo(self):
        r = self.client.post(self.REGISTRO_URL, self.DATOS_VALIDOS, follow=True)
        self.assertRedirects(r, "/catalogo/")

    def test_email_duplicado_muestra_error(self):
        make_user("nuevo@test.com")
        r = self.client.post(self.REGISTRO_URL, self.DATOS_VALIDOS)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Ya existe")

    def test_contrasena_debil_muestra_error(self):
        datos = {**self.DATOS_VALIDOS, "password1": "sinmayuscula1!", "password2": "sinmayuscula1!"}
        r = self.client.post(self.REGISTRO_URL, datos)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "mayúscula")


# ── Guardas de permiso ────────────────────────────────────────────────────────

class GuardaPermisoTest(TestCase):
    def setUp(self):
        self.cliente = make_user("c@test.com", User.Rol.CLIENTE)
        self.ventas = make_user("v@test.com", User.Rol.VENTAS)
        self.gerencia = make_user("g@test.com", User.Rol.GERENCIA)

    def test_no_autenticado_redirige_al_login(self):
        for url in ["/catalogo/", "/dashboard/", "/pedidos/operativo/"]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, f"Falla en {url}")
            self.assertIn("/cuentas/login/", r["Location"])

    def test_cliente_no_puede_ver_dashboard(self):
        self.client.force_login(self.cliente)
        r = self.client.get("/dashboard/")
        self.assertEqual(r.status_code, 403)

    def test_cliente_no_puede_ver_operativo(self):
        self.client.force_login(self.cliente)
        r = self.client.get("/pedidos/operativo/")
        self.assertEqual(r.status_code, 403)

    def test_cliente_puede_ver_catalogo(self):
        self.client.force_login(self.cliente)
        r = self.client.get("/catalogo/")
        self.assertEqual(r.status_code, 200)

    def test_ventas_puede_ver_operativo(self):
        self.client.force_login(self.ventas)
        r = self.client.get("/pedidos/operativo/")
        self.assertEqual(r.status_code, 200)

    def test_ventas_no_puede_ver_dashboard(self):
        self.client.force_login(self.ventas)
        r = self.client.get("/dashboard/")
        self.assertEqual(r.status_code, 403)

    def test_gerencia_puede_ver_dashboard(self):
        self.client.force_login(self.gerencia)
        r = self.client.get("/dashboard/")
        self.assertEqual(r.status_code, 200)

    def test_gerencia_puede_ver_operativo(self):
        self.client.force_login(self.gerencia)
        r = self.client.get("/pedidos/operativo/")
        self.assertEqual(r.status_code, 200)
