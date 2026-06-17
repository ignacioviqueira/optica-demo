from django.urls import path

from .views import detalle, index

app_name = "catalogo"

urlpatterns = [
    path("", index, name="index"),
    path("<int:pk>/", detalle, name="detalle"),
]
