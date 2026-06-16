from django.contrib import admin
from django.urls import include, path

from apps.catalogo.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("cuentas/", include("apps.cuentas.urls")),
    path("catalogo/", include("apps.catalogo.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("pedidos/", include("apps.pedidos.urls")),
]
