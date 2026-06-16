from django.urls import path

from .views import index

app_name = "catalogo"

urlpatterns = [
    path("", index, name="index"),
]
