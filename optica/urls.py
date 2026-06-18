from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.catalogo.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("cuentas/", include("apps.cuentas.urls")),
    path("catalogo/", include("apps.catalogo.urls")),
    path("inventario/", include("apps.inventario.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("pedidos/", include("apps.pedidos.urls")),
    # VTO — Prueba Virtual
    path("vto/", include("apps.vto.urls")),
    # API REST (DRF)
    path("api/", include("apps.inventario.api_urls")),
    path("api/vto/", include("apps.vto.api_urls")),
    path("api/", include("apps.pedidos.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
