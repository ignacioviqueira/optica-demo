from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0003_producto_imagen_charfield"),
    ]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="imagen_vto",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.CreateModel(
            name="ProductoImagen",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("imagen", models.CharField(max_length=200)),
                ("orden", models.PositiveSmallIntegerField(default=0)),
                (
                    "producto",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="imagenes",
                        to="inventario.producto",
                    ),
                ),
            ],
            options={
                "verbose_name": "Imagen de producto",
                "verbose_name_plural": "Imágenes de producto",
                "ordering": ["orden"],
            },
        ),
    ]
