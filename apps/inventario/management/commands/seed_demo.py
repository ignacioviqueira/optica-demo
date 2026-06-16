"""
Carga datos de ejemplo para el demo de la óptica.
Idempotente: usar get_or_create para no duplicar registros.
"""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.inventario.models import Categoria, Producto
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
            "nombre": "Wayfarer Clásico",
            "marca": "Ray-Ban",
            "descripcion": "El ícono atemporal. Acetato negro, lente G-15.",
            "precio": Decimal("45000.00"),
            "stock_actual": 15,
            "stock_minimo": 3,
        },
        {
            "nombre": "Holbrook",
            "marca": "Oakley",
            "descripcion": "Estilo deportivo con montura de acetato premium.",
            "precio": Decimal("38000.00"),
            "stock_actual": 8,
            "stock_minimo": 3,
        },
        {
            "nombre": "PR 01OS",
            "marca": "Prada",
            "descripcion": "Diseño geométrico de alta gama en acetato negro.",
            "precio": Decimal("120000.00"),
            "stock_actual": 2,   # ← stock crítico
            "stock_minimo": 3,
        },
        {
            "nombre": "FT5634-B",
            "marca": "Tom Ford",
            "descripcion": "Elegancia italiana, montura cuadrada en acetato.",
            "precio": Decimal("95000.00"),
            "stock_actual": 1,   # ← stock crítico
            "stock_minimo": 3,
        },
        {
            "nombre": "205/V/4-F 55",
            "marca": "Carrera",
            "descripcion": "Montura deportiva urbana con puente doble.",
            "precio": Decimal("32000.00"),
            "stock_actual": 12,
            "stock_minimo": 3,
        },
    ],
    "Cristales": [
        {
            "nombre": "Varilux X Series",
            "marca": "Essilor",
            "descripcion": "Progresivo de última generación, sin saltos de imagen.",
            "precio": Decimal("65000.00"),
            "stock_actual": 20,
            "stock_minimo": 5,
        },
        {
            "nombre": "Individual 2",
            "marca": "Zeiss",
            "descripcion": "Personalizado según geometría facial del paciente.",
            "precio": Decimal("85000.00"),
            "stock_actual": 10,
            "stock_minimo": 5,
        },
        {
            "nombre": "ID MyStyle V+",
            "marca": "Hoya",
            "descripcion": "Progresivo adaptativo para uso digital intensivo.",
            "precio": Decimal("72000.00"),
            "stock_actual": 4,   # ← stock crítico
            "stock_minimo": 5,
        },
        {
            "nombre": "SeeMax Ultimate",
            "marca": "Nikon",
            "descripcion": "Freeform con optimización binocular.",
            "precio": Decimal("78000.00"),
            "stock_actual": 7,
            "stock_minimo": 5,
        },
        {
            "nombre": "Autograph III",
            "marca": "Shamir",
            "descripcion": "Progresivo free-form de campo amplio.",
            "precio": Decimal("68000.00"),
            "stock_actual": 6,
            "stock_minimo": 5,
        },
    ],
    "Lentes de Contacto": [
        {
            "nombre": "Oasys 1-Day (30 u.)",
            "marca": "Acuvue",
            "descripcion": "Desechables diarias con tecnología HydraLuxe.",
            "precio": Decimal("18500.00"),
            "stock_actual": 50,
            "stock_minimo": 10,
        },
        {
            "nombre": "Ultra (6 u.)",
            "marca": "Bausch+Lomb",
            "descripcion": "Mensuales con MoistureSeal para ojo seco.",
            "precio": Decimal("22000.00"),
            "stock_actual": 3,   # ← stock crítico
            "stock_minimo": 10,
        },
        {
            "nombre": "Biofinity (6 u.)",
            "marca": "CooperVision",
            "descripcion": "Mensuales con material Aquaform.",
            "precio": Decimal("19500.00"),
            "stock_actual": 25,
            "stock_minimo": 10,
        },
        {
            "nombre": "Dailies Total1 (30 u.)",
            "marca": "Alcon",
            "descripcion": "Diarias water-gradient para máxima comodidad.",
            "precio": Decimal("21000.00"),
            "stock_actual": 15,
            "stock_minimo": 10,
        },
        {
            "nombre": "Proclear Compatibles (6 u.)",
            "marca": "CooperVision",
            "descripcion": "Mensuales PC Technology, aptas para ojo seco.",
            "precio": Decimal("15000.00"),
            "stock_actual": 2,   # ← stock crítico
            "stock_minimo": 10,
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
                    },
                )
                if created:
                    prod_created += 1
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
        wayfarer = productos.get("Ray-Ban_Wayfarer Clásico")
        varilux = productos.get("Essilor_Varilux X Series")
        oasys = productos.get("Acuvue_Oasys 1-Day (30 u.)")
        ultra = productos.get("Bausch+Lomb_Ultra (6 u.)")
        holbrook = productos.get("Oakley_Holbrook")
        zeiss = productos.get("Zeiss_Individual 2")

        specs = [
            # (estado, fecha_offset_dias, receta_idx, [(producto, cantidad)], motivo)
            (
                Pedido.Estado.PENDIENTE_VALIDACION,
                2,
                0,
                [(wayfarer, 1), (varilux, 1)],
                "",
            ),
            (
                Pedido.Estado.EN_PROCESO,
                5,
                1,
                [(holbrook, 1), (zeiss, 1)],
                "",
            ),
            (
                Pedido.Estado.LISTO,
                10,
                0,
                [(oasys, 2)],
                "",
            ),
            (
                Pedido.Estado.LISTO,
                20,
                None,
                [(ultra, 1)],
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
