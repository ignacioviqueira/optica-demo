from django.urls import path

from .views import RegistrarEventoVTOView

urlpatterns = [
    path('evento/', RegistrarEventoVTOView.as_view(), name='vto-evento'),
]
