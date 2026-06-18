from django.urls import path

from .views import export_csv, index

app_name = "dashboard"

urlpatterns = [
    path("", index, name="index"),
    path("export/csv/", export_csv, name="export_csv"),
]
