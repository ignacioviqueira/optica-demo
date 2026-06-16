from functools import wraps

from django.conf import settings
from django.shortcuts import redirect, render


def login_requerido(view_func):
    """Redirige al login si el usuario no está autenticado."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return view_func(request, *args, **kwargs)
    return wrapper


def rol_requerido(*roles):
    """
    Restringe el acceso a usuarios con alguno de los roles indicados.
    - No autenticado → redirige al login.
    - Autenticado sin rol → 403.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")
            if request.user.rol not in roles:
                return render(request, "403.html", status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
