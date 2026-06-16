from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class CustomUserTest(TestCase):
    def test_email_es_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_rol_default_es_cliente(self):
        user = User.objects.create_user(
            email="test@optica.demo", username="test", password="Test@123"
        )
        self.assertEqual(user.rol, User.Rol.CLIENTE)

    def test_str_devuelve_email(self):
        user = User.objects.create_user(
            email="str@optica.demo", username="strtest", password="Test@123"
        )
        self.assertEqual(str(user), "str@optica.demo")

    def test_roles_disponibles(self):
        roles = [r.value for r in User.Rol]
        self.assertIn("cliente", roles)
        self.assertIn("ventas", roles)
        self.assertIn("gerencia", roles)
