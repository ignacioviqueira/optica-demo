from datetime import timedelta
from math import ceil

from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import LoginForm, RegisterForm

User = get_user_model()

MAX_INTENTOS = 5
BLOQUEO_MINUTOS = 15


# ── Helpers ───────────────────────────────────────────────────────────────────

def _redirigir_por_rol(user):
    if user.rol == User.Rol.GERENCIA:
        return redirect("dashboard:index")
    if user.rol == User.Rol.VENTAS:
        return redirect("pedidos:operativo")
    return redirect("catalogo:index")


# ── Login ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return _redirigir_por_rol(request.user)

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].lower()
        password = form.cleaned_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            form.add_error(None, "Correo o contraseña incorrectos.")
            return render(request, "cuentas/login.html", {"form": form})

        # Bloqueo vigente
        if user.is_locked:
            mins = ceil((user.locked_until - timezone.now()).total_seconds() / 60)
            form.add_error(
                None,
                f"Cuenta bloqueada temporalmente. Intente nuevamente en {mins} minuto(s).",
            )
            return render(request, "cuentas/login.html", {"form": form})

        # Bloqueo expirado: resetear contador
        if user.locked_until and not user.is_locked:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save(update_fields=["failed_login_attempts", "locked_until"])

        auth_user = authenticate(request, username=email, password=password)

        if auth_user is not None:
            auth_user.failed_login_attempts = 0
            auth_user.locked_until = None
            auth_user.save(update_fields=["failed_login_attempts", "locked_until"])
            login(request, auth_user)
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)
            return _redirigir_por_rol(auth_user)

        # Contraseña incorrecta
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_INTENTOS:
            user.locked_until = timezone.now() + timedelta(minutes=BLOQUEO_MINUTOS)
            form.add_error(
                None,
                f"Demasiados intentos fallidos. Cuenta bloqueada por {BLOQUEO_MINUTOS} minutos.",
            )
        else:
            restantes = MAX_INTENTOS - user.failed_login_attempts
            form.add_error(
                None,
                f"Correo o contraseña incorrectos. "
                f"Intentos restantes antes del bloqueo: {restantes}.",
            )
        user.save(update_fields=["failed_login_attempts", "locked_until"])

    return render(request, "cuentas/login.html", {"form": form})


# ── Registro ──────────────────────────────────────────────────────────────────

def registro_view(request):
    if request.user.is_authenticated:
        return _redirigir_por_rol(request.user)

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("catalogo:index")

    return render(request, "cuentas/registro.html", {"form": form})


# ── Logout ────────────────────────────────────────────────────────────────────

class LogoutView(DjangoLogoutView):
    """POST-only logout que redirige al login."""
    next_page = "cuentas:login"
