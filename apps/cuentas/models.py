from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Rol(models.TextChoices):
        CLIENTE = "cliente", "Cliente"
        VENTAS = "ventas", "Ventas"
        GERENCIA = "gerencia", "Gerencia"

    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.CLIENTE)

    # Bloqueo temporal tras intentos fallidos (HU-01)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.email

    @property
    def is_locked(self):
        from django.utils import timezone
        return self.locked_until is not None and self.locked_until > timezone.now()
