from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0004_producto_imagen_vto_productoimagen"),
    ]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="color",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="producto",
            name="medidas",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="producto",
            name="caracteristicas",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
