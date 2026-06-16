from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Rol(models.TextChoices):
        CLIENTE = "cliente", "Cliente"
        VENTAS = "ventas", "Ventas"
        GERENCIA = "gerencia", "Gerencia"

    # Usamos email como identificador único (según la tesis)
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.CLIENTE)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
