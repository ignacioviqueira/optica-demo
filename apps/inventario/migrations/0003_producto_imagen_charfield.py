from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0002_producto_activo_producto_forma_producto_material"),
    ]

    operations = [
        migrations.AlterField(
            model_name="producto",
            name="imagen",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
    ]
