from django.urls import path

from .views import LogoutView, login_view, registro_view

app_name = "cuentas"

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("registro/", registro_view, name="registro"),
]
