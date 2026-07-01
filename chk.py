from apps.inventario.models import Producto, ProductoImagen
arms = Producto.objects.filter(categoria__nombre="Armazones")
for a in arms:
    print("OK" if a.activo else "OFF", a.pk, a.nombre[:28].ljust(28), a.imagen_vto or "NO_VTO")
print("ProductoImagen total:", ProductoImagen.objects.count())
arm_with_vto = arms.filter(activo=True).exclude(imagen_vto="").first()
print("Armazon con VTO para test:", arm_with_vto.pk if arm_with_vto else "NINGUNO")
