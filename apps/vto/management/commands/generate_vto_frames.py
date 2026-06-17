"""
Genera 4 PNGs de armazones con fondo transparente para el módulo VTO.
Usa Pillow (ya incluido en requirements.txt).

Uso:
    python manage.py generate_vto_frames
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

W, H = 640, 220


def _make_img():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def _draw_clasico() -> Image.Image:
    """Clásico / Wayfarer: rectángulos redondeados, marco plástico oscuro."""
    img = _make_img()
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    c = (28, 22, 15, 255)
    lw = 10
    d.rounded_rectangle([38, cy - 52, cx - 18, cy + 52], radius=14, outline=c, width=lw)
    d.rounded_rectangle([cx + 18, cy - 52, W - 38, cy + 52], radius=14, outline=c, width=lw)
    d.line([(cx - 18, cy - 10), (cx + 18, cy - 10)], fill=c, width=lw - 4)
    d.line([(cx - 18, cy + 4), (cx + 18, cy + 4)], fill=c, width=lw - 5)
    d.ellipse([cx - 28, cy - 14, cx - 16, cy - 2], fill=c)
    d.ellipse([cx + 16, cy - 14, cx + 28, cy - 2], fill=c)
    d.line([(38, cy - 35), (0, cy - 46)], fill=c, width=lw - 2)
    d.line([(W - 38, cy - 35), (W, cy - 46)], fill=c, width=lw - 2)
    return img


def _draw_aviador() -> Image.Image:
    """Aviador: forma de lágrima, marco metálico dorado delgado."""
    img = _make_img()
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    gold = (190, 148, 28, 255)
    lw = 5
    # lentes — elipses desplazadas hacia arriba para forma de lágrima
    d.ellipse([35, cy - 42, cx - 20, cy + 68], outline=gold, width=lw)
    d.ellipse([cx + 20, cy - 42, W - 35, cy + 68], outline=gold, width=lw)
    # barra superior que une los lentes
    d.line([(35, cy - 42), (cx - 20, cy - 42)], fill=gold, width=lw)
    d.line([(cx + 20, cy - 42), (W - 35, cy - 42)], fill=gold, width=lw)
    # puente curvo doble
    d.arc([cx - 32, cy - 56, cx + 32, cy - 34], 0, 180, fill=gold, width=lw - 1)
    # patillas
    d.line([(35, cy - 42), (0, cy - 58)], fill=gold, width=lw)
    d.line([(W - 35, cy - 42), (W, cy - 58)], fill=gold, width=lw)
    return img


def _draw_redondo() -> Image.Image:
    """Redondo: monturas circulares, aro fino negro."""
    img = _make_img()
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    c = (38, 38, 38, 255)
    lw = 6
    r = 70
    lc = cx - r - 22   # center x left lens
    rc = cx + r + 22   # center x right lens
    d.ellipse([lc - r, cy - r, lc + r, cy + r], outline=c, width=lw)
    d.ellipse([rc - r, cy - r, rc + r, cy + r], outline=c, width=lw)
    d.line([(lc + r, cy - 8), (rc - r, cy - 8)], fill=c, width=lw - 2)
    d.line([(lc - r, cy - 22), (0, cy - 32)], fill=c, width=lw)
    d.line([(rc + r, cy - 22), (W, cy - 32)], fill=c, width=lw)
    return img


def _draw_deportivo() -> Image.Image:
    """Deportivo: montura wrap-around con acento de color."""
    img = _make_img()
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    negro = (14, 14, 14, 255)
    rojo  = (200, 40, 40, 255)
    lw = 9
    # cuerpo principal
    d.rounded_rectangle([22, cy - 52, W - 22, cy + 52], radius=24, outline=negro, width=lw)
    # divisor central
    d.rectangle([cx - 4, cy - 46, cx + 4, cy + 46], fill=negro)
    # franja de acento superior
    d.rounded_rectangle([22, cy - 52, W - 22, cy - 30], radius=20, fill=rojo)
    d.rounded_rectangle([26, cy - 48, W - 26, cy - 34], radius=16, fill=(14, 14, 14, 210))
    # patillas
    d.line([(22, cy - 8), (0, cy - 4)], fill=negro, width=lw)
    d.line([(W - 22, cy - 8), (W, cy - 4)], fill=negro, width=lw)
    return img


_FRAMES = {
    "clasico":   _draw_clasico,
    "aviador":   _draw_aviador,
    "redondo":   _draw_redondo,
    "deportivo": _draw_deportivo,
}


class Command(BaseCommand):
    help = "Genera los 4 PNG de armazones VTO en static/vto/frames/"

    def handle(self, *args, **options):
        out_dir = Path(settings.BASE_DIR) / "static" / "vto" / "frames"
        out_dir.mkdir(parents=True, exist_ok=True)

        for name, fn in _FRAMES.items():
            path = out_dir / f"{name}.png"
            fn().save(path, "PNG")
            self.stdout.write(self.style.SUCCESS(f"  ✓ {path.name}"))

        self.stdout.write(self.style.SUCCESS("Frames VTO generados exitosamente."))
