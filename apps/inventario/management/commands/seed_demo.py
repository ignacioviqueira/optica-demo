"""
Carga datos de ejemplo para el demo de la óptica.
Idempotente: usar get_or_create para no duplicar registros.
"""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.inventario.models import Categoria, Producto, ProductoImagen
from apps.pedidos.models import DetallePedido, Pedido, Receta

User = get_user_model()

# ── Credenciales de demo ──────────────────────────────────────────────────────
USUARIOS = [
    {
        "email": "gerencia@optica.demo",
        "username": "gerencia",
        "password": "Gerencia@123",
        "first_name": "Laura",
        "last_name": "Gómez",
        "rol": "gerencia",
        "is_staff": True,
        "is_superuser": False,
    },
    {
        "email": "ventas@optica.demo",
        "username": "ventas",
        "password": "Ventas@123",
        "first_name": "Marcos",
        "last_name": "Pereyra",
        "rol": "ventas",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "cliente@optica.demo",
        "username": "cliente",
        "password": "Cliente@123",
        "first_name": "Ana",
        "last_name": "Rodríguez",
        "rol": "cliente",
        "is_staff": False,
        "is_superuser": False,
    },
]

# ── Catálogo de productos ──────────────────────────────────────────────────────
PRODUCTOS = {
    "Armazones": [
        {
            "slug": "rayban_clubmaster",
            "nombre": "Clubmaster Optics",
            "marca": "Ray-Ban",
            "descripcion": "El clásico browline que convirtió a Ray-Ban en la marca icónica que es. Con sus patillas finas y su audaz montura semi-rimless, sigue dejando su huella día a día.",
            "precio": Decimal("142000.00"),
            "stock_actual": 8,
            "stock_minimo": 3,
            "material": "Acetato y metal",
            "forma": "Browline",
            "color": "Negro",
            "medidas": "4,9 – 2,1 – 14,0 cm",
            "caracteristicas": ["Diseño browline", "Montura semi-rimless", "Plaquetas ajustables"],
            "imagen": "productos/rayban_clubmaster_1.png",
            "imagen_vto": "productos/rayban_clubmaster_vto.png",
        },
        {
            "slug": "rayban_aviator",
            "nombre": "Aviator Optics",
            "marca": "Ray-Ban",
            "descripcion": "El armazón en forma de gota del Ray-Ban Aviator es un giro distintivo sobre el clásico estilo aviador. Con su doble puente y su montura fina pero resistente, va igual de bien para pasear en moto que para volar a gran altura.",
            "precio": Decimal("135000.00"),
            "stock_actual": 6,
            "stock_minimo": 3,
            "material": "Metal",
            "forma": "Aviador",
            "color": "Dorado",
            "medidas": "5,8 – 1,4 – 13,5 cm",
            "caracteristicas": ["Doble puente", "Plaquetas ajustables", "Lentes en gota"],
            "imagen": "productos/rayban_aviator_1.png",
            "imagen_vto": "productos/rayban_aviator_vto.png",
        },
        {
            "slug": "rayban_wayfarer",
            "nombre": "Wayfarer Ease",
            "marca": "Ray-Ban",
            "descripcion": "Un clásico Wayfarer que nunca pasa de moda. Hecho en acetato flexible, luce elegantes remaches plateados y patillas finas de tonalidad rica y multicapa.",
            "precio": Decimal("121000.00"),
            "stock_actual": 12,
            "stock_minimo": 4,
            "material": "Acetato",
            "forma": "Cuadrado",
            "color": "Negro brillante",
            "medidas": "5,0 – 2,2 – 15,0 cm",
            "caracteristicas": ["Acetato flexible", "Remaches plateados", "Plaquetas integradas"],
            "imagen": "productos/rayban_wayfarer_1.png",
            "imagen_vto": "productos/rayban_wayfarer_vto.png",
        },
        {
            "slug": "rayban_round",
            "nombre": "Round Metal Optics",
            "marca": "Ray-Ban",
            "descripcion": "Un armazón perfectamente redondo con el diseño icónico de Ray-Ban. Construido en metal liviano, luce patillas estilizadas y un estilo audaz que no pasa desapercibido.",
            "precio": Decimal("128000.00"),
            "stock_actual": 5,
            "stock_minimo": 3,
            "material": "Metal",
            "forma": "Redondo",
            "color": "Dorado",
            "medidas": "5,0 – 2,1 – 14,5 cm",
            "caracteristicas": ["Forma redonda", "Plaquetas ajustables", "Patillas estilizadas"],
            "imagen": "productos/rayban_round_1.png",
            "imagen_vto": "productos/rayban_round_vto.png",
        },
        {
            "slug": "oakley_holbrook",
            "nombre": "Holbrook RX",
            "marca": "Oakley",
            "descripcion": "La versión óptica de uno de los estilos insignia de Oakley. Apariencia cuadrada y audaz, con puente tipo llave, patillas estilizadas y plaquetas moldeadas.",
            "precio": Decimal("112000.00"),
            "stock_actual": 9,
            "stock_minimo": 4,
            "material": "O-Matter",
            "forma": "Cuadrado",
            "color": "Negro",
            "medidas": "5,6 – 1,8 – 13,7 cm",
            "caracteristicas": ["Puente tipo llave", "Plaquetas integradas", "Bisagras con resorte"],
            "imagen": "productos/oakley_holbrook_1.png",
            "imagen_vto": "productos/oakley_holbrook_vto.png",
        },
        {
            "slug": "oakley_crosslink",
            "nombre": "Crosslink",
            "marca": "Oakley",
            "descripcion": "Un armazón auténticamente cool, fabricado a mano en O-Matter liviano y resistente. Patillas robustas y ajustables para un calce óptimo, con terminaciones Unobtainium antideslizantes.",
            "precio": Decimal("118000.00"),
            "stock_actual": 3,
            "stock_minimo": 4,
            "material": "O-Matter",
            "forma": "Rectangular",
            "color": "Negro",
            "medidas": "5,6 – 1,6 – 13,8 cm",
            "caracteristicas": ["O-Matter resistente", "Patillas ajustables", "Unobtainium antideslizante"],
            "imagen": "productos/oakley_crosslink_1.png",
            "imagen_vto": "productos/oakley_crosslink_vto.png",
        },
        {
            "slug": "oakley_airdrop",
            "nombre": "Airdrop",
            "marca": "Oakley",
            "descripcion": "Un armazón de estética futurista, fabricado a mano en O-Matter ultraresistente y liviano, con patillas robustas y un diseño angular.",
            "precio": Decimal("108000.00"),
            "stock_actual": 7,
            "stock_minimo": 4,
            "material": "O-Matter",
            "forma": "Rectangular",
            "color": "Negro",
            "medidas": "5,7 – 1,8 – 14,3 cm",
            "caracteristicas": ["O-Matter ultraresistente", "Plaquetas integradas", "Diseño angular"],
            "imagen": "productos/oakley_airdrop_1.png",
            "imagen_vto": "productos/oakley_airdrop_vto.png",
        },
    ],
}

# ── Recetas de demo para la usuaria cliente ────────────────────────────────────
RECETAS = [
    {
        "esfera_od": Decimal("-2.50"),
        "cilindro_od": Decimal("-0.75"),
        "eje_od": 170,
        "dnp": Decimal("64.00"),
        "fecha_emision": datetime.date(2025, 1, 15),
    },
    {
        "esfera_od": Decimal("-3.00"),
        "cilindro_od": Decimal("-1.00"),
        "eje_od": 165,
        "dnp": Decimal("63.50"),
        "fecha_emision": datetime.date(2024, 6, 10),
    },
    {
        "esfera_od": Decimal("-2.25"),
        "cilindro_od": Decimal("-0.50"),
        "eje_od": 175,
        "dnp": Decimal("64.50"),
        "fecha_emision": datetime.date(2023, 12, 1),
    },
]


class Command(BaseCommand):
    help = "Carga datos de ejemplo para el demo. Idempotente."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Sembrando datos de demo..."))

        usuarios = self._seed_usuarios()
        categorias, productos = self._seed_catalogo()
        recetas = self._seed_recetas(usuarios["cliente"])
        self._seed_pedidos(usuarios["cliente"], productos, recetas)

        self.stdout.write(self.style.SUCCESS("\n✓ Seed completado"))
        self._print_credentials()

    # ── Usuarios ──────────────────────────────────────────────────────────────

    def _seed_usuarios(self):
        self.stdout.write("  → Usuarios...", ending="")
        result = {}
        created_count = 0
        for data in USUARIOS:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "username": data["username"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "rol": data["rol"],
                    "is_staff": data["is_staff"],
                    "is_superuser": data["is_superuser"],
                },
            )
            if created:
                user.set_password(data["password"])
                user.save()
                created_count += 1
            result[data["rol"]] = user
        self.stdout.write(self.style.SUCCESS(f" {created_count} nuevos, {len(USUARIOS) - created_count} ya existían"))
        return result

    # ── Catálogo ──────────────────────────────────────────────────────────────

    def _seed_catalogo(self):
        self.stdout.write("  → Categorías y productos...", ending="")
        categorias = {}
        productos = {}
        cat_created = prod_created = 0

        # Desactivar productos de categorías que ya no están en el seed
        Producto.objects.exclude(
            categoria__nombre__in=list(PRODUCTOS.keys())
        ).filter(activo=True).update(activo=False)

        # Desactivar productos dentro de categorías activas que ya no están en el seed
        nombres_actuales = [item["nombre"] for items in PRODUCTOS.values() for item in items]
        Producto.objects.filter(
            categoria__nombre__in=list(PRODUCTOS.keys())
        ).exclude(nombre__in=nombres_actuales).update(activo=False)

        for nombre_cat, items in PRODUCTOS.items():
            cat, created = Categoria.objects.get_or_create(
                nombre=nombre_cat,
                defaults={"descripcion": f"Categoría: {nombre_cat}"},
            )
            if created:
                cat_created += 1
            categorias[nombre_cat] = cat

            for item in items:
                prod, created = Producto.objects.get_or_create(
                    nombre=item["nombre"],
                    marca=item["marca"],
                    defaults={
                        "descripcion": item["descripcion"],
                        "precio": item["precio"],
                        "stock_actual": item["stock_actual"],
                        "stock_minimo": item["stock_minimo"],
                        "categoria": cat,
                        "material": item.get("material", ""),
                        "forma": item.get("forma", ""),
                        "imagen": item.get("imagen", ""),
                        "imagen_vto": item.get("imagen_vto", ""),
                        "activo": True,
                    },
                )
                if created:
                    prod_created += 1
                else:
                    # Re-aplicar todos los campos del seed (idempotente)
                    campos = (
                        "descripcion", "material", "forma", "imagen", "imagen_vto",
                        "color", "medidas", "caracteristicas",
                    )
                    for campo in campos:
                        default = [] if campo == "caracteristicas" else ""
                        setattr(prod, campo, item.get(campo, default))
                    prod.activo = True
                    prod.save(update_fields=[*campos, "activo"])

                # Galería extra: {slug}_2.png y {slug}_3.png para armazones
                slug = item.get("slug")
                if slug and nombre_cat == "Armazones":
                    prod.imagenes.all().delete()
                    ProductoImagen.objects.create(
                        producto=prod,
                        imagen=f"productos/{slug}_2.png",
                        orden=1,
                    )
                    ProductoImagen.objects.create(
                        producto=prod,
                        imagen=f"productos/{slug}_3.png",
                        orden=2,
                    )

                productos[f"{item['marca']}_{item['nombre']}"] = prod

        self.stdout.write(
            self.style.SUCCESS(f" {cat_created} cats · {prod_created} productos nuevos")
        )
        return categorias, productos

    # ── Recetas ───────────────────────────────────────────────────────────────

    def _seed_recetas(self, cliente):
        self.stdout.write("  → Recetas...", ending="")
        recetas = []
        created_count = 0
        for data in RECETAS:
            receta, created = Receta.objects.get_or_create(
                usuario=cliente,
                fecha_emision=data["fecha_emision"],
                defaults={
                    "esfera_od": data["esfera_od"],
                    "cilindro_od": data["cilindro_od"],
                    "eje_od": data["eje_od"],
                    "dnp": data["dnp"],
                },
            )
            if created:
                created_count += 1
            recetas.append(receta)
        self.stdout.write(self.style.SUCCESS(f" {created_count} nuevas"))
        return recetas

    # ── Pedidos ───────────────────────────────────────────────────────────────

    def _seed_pedidos(self, cliente, productos, recetas):
        self.stdout.write("  → Pedidos...", ending="")

        if Pedido.objects.filter(usuario=cliente).count() >= 5:
            self.stdout.write(self.style.WARNING(" ya existen, se omiten"))
            return

        today = timezone.now()
        wayfarer  = productos.get("Ray-Ban_Wayfarer Ease")
        aviator   = productos.get("Ray-Ban_Aviator Optics")
        holbrook  = productos.get("Oakley_Holbrook RX")
        round_m   = productos.get("Ray-Ban_Round Metal Optics")
        clubmaster = productos.get("Ray-Ban_Clubmaster Optics")
        crosslink  = productos.get("Oakley_Crosslink")

        specs = [
            # (estado, fecha_offset_dias, receta_idx, [(producto, cantidad)], motivo)
            (
                Pedido.Estado.PENDIENTE_VALIDACION,
                2,
                0,
                [(wayfarer, 1), (aviator, 1)],
                "",
            ),
            (
                Pedido.Estado.EN_PROCESO,
                5,
                1,
                [(holbrook, 1), (round_m, 1)],
                "",
            ),
            (
                Pedido.Estado.LISTO,
                10,
                0,
                [(clubmaster, 1)],
                "",
            ),
            (
                Pedido.Estado.LISTO,
                20,
                None,
                [(crosslink, 1)],
                "",
            ),
            (
                Pedido.Estado.RECHAZADO,
                15,
                2,
                [(wayfarer, 1)],
                "La receta presentada está vencida (más de 1 año de antigüedad).",
            ),
        ]

        created = 0
        for estado, offset, receta_idx, items, motivo in specs:
            total = sum(p.precio * c for p, c in items if p)
            receta = recetas[receta_idx] if receta_idx is not None else None

            pedido = Pedido.objects.create(
                usuario=cliente,
                total=total,
                estado=estado,
                receta=receta,
                motivo_rechazo=motivo,
            )
            # Retrofechar manualmente
            Pedido.objects.filter(pk=pedido.pk).update(
                fecha=today - datetime.timedelta(days=offset)
            )

            for prod, qty in items:
                if prod:
                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=prod,
                        cantidad=qty,
                        precio_unitario=prod.precio,
                    )
            created += 1

        self.stdout.write(self.style.SUCCESS(f" {created} creados"))

    # ── Resumen de credenciales ───────────────────────────────────────────────

    def _print_credentials(self):
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Credenciales de acceso:"))
        rows = [
            ("Gerencia", "gerencia@optica.demo", "Gerencia@123"),
            ("Ventas",   "ventas@optica.demo",   "Ventas@123"),
            ("Cliente",  "cliente@optica.demo",   "Cliente@123"),
        ]
        for rol, email, pwd in rows:
            self.stdout.write(f"  [{rol:8s}]  {email}  /  {pwd}")
