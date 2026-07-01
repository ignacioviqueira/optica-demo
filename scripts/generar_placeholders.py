"""
scripts/generar_placeholders.py
Genera imágenes PNG de placeholder para todos los productos del demo.
Solo requiere Pillow (ya en requirements.txt). No necesita rembg ni red.

Uso (desde la raíz del repo):
    docker compose run --rm web python scripts/generar_placeholders.py
    # o localmente si tenés Python + Pillow:
    python scripts/generar_placeholders.py

Los PNGs se guardan en static/productos/ y deben commiterse al repositorio.
Para armazones genera un PNG con canal alpha (fondo transparente) listo para el VTO.
Para cristales y lentes genera un PNG con fondo de color sólido.
"""

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT  = Path(__file__).resolve().parent.parent
SALIDA_DIR = REPO_ROOT / "static" / "productos"
SALIDA_DIR.mkdir(parents=True, exist_ok=True)

ANCHO = 600
ALTO  = 300


# ── Helpers de dibujo ─────────────────────────────────────────────────────────

def _fuente(size: int):
    """Carga una fuente TrueType si está disponible; cae a la default de Pillow."""
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        try:
            return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except Exception:
            return ImageFont.load_default()


def _guardar(img: Image.Image, nombre: str) -> None:
    destino = SALIDA_DIR / nombre
    img.save(destino, format="PNG", optimize=True)
    print(f"  [ok] {nombre}")


# ── Generadores por tipo ──────────────────────────────────────────────────────

def _armazon_png(nombre_archivo: str, label: str, color_frame=(30, 30, 30)) -> None:
    """
    Dibuja un armazón de gafas esquemático sobre fondo TRANSPARENTE (RGBA).
    Resultado: PNG con alpha channel listo para el overlay VTO.
    """
    img = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    cx, cy = ANCHO // 2, ALTO // 2
    lw = 8        # grosor de línea
    # Dimensiones de cada lente
    lw_lens = 190
    lh_lens = 120
    gap = 30      # espacio entre lentes (bridge)

    # Ojo izquierdo
    lx = cx - gap // 2 - lw_lens
    rx = cx - gap // 2
    d.rounded_rectangle(
        [lx, cy - lh_lens // 2, rx, cy + lh_lens // 2],
        radius=28, outline=color_frame, width=lw,
    )

    # Ojo derecho
    lx2 = cx + gap // 2
    rx2 = cx + gap // 2 + lw_lens
    d.rounded_rectangle(
        [lx2, cy - lh_lens // 2, rx2, cy + lh_lens // 2],
        radius=28, outline=color_frame, width=lw,
    )

    # Puente (bridge)
    bridge_y = cy - 8
    d.line([(rx, bridge_y), (lx2, bridge_y)], fill=color_frame, width=lw - 2)

    # Patillas (temples) — líneas diagonales hacia los lados
    d.line([(lx, cy), (18, cy - 20)], fill=color_frame, width=lw - 2)
    d.line([(rx2, cy), (ANCHO - 18, cy - 20)], fill=color_frame, width=lw - 2)

    # Texto con el label (opcionalmente oscuro para ser visible en preview)
    font = _fuente(16)
    d.text((cx, ALTO - 28), label, fill=(*color_frame, 200), font=font, anchor="mm")

    _guardar(img, nombre_archivo)


def _producto_png(
    nombre_archivo: str, label: str,
    color_fondo=(245, 248, 252), color_acento=(70, 130, 200),
) -> None:
    """
    Genera un PNG de producto estándar (fondo sólido, ícono y texto).
    Usado para cristales y lentes de contacto.
    """
    img = Image.new("RGB", (ANCHO, ALTO), color_fondo)
    d = ImageDraw.Draw(img)

    # Banda de color en el borde superior
    d.rectangle([0, 0, ANCHO, 8], fill=color_acento)

    # Círculo decorativo central
    cx, cy = ANCHO // 2, ALTO // 2 - 20
    r = 65
    d.ellipse([cx - r, cy - r, cx + r, cy + r],
              outline=color_acento, width=6)
    d.ellipse([cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14],
              outline=(*color_acento, 80), width=3)

    # Label
    font_grande = _fuente(22)
    font_chico  = _fuente(14)
    lineas = label.split(" — ", 1)
    if len(lineas) == 2:
        d.text((cx, ALTO - 55), lineas[0], fill=color_acento, font=font_grande, anchor="mm")
        d.text((cx, ALTO - 28), lineas[1], fill=(100, 110, 120), font=font_chico, anchor="mm")
    else:
        d.text((cx, ALTO - 40), label, fill=color_acento, font=font_grande, anchor="mm")

    _guardar(img, nombre_archivo)


# ── Tabla de productos ────────────────────────────────────────────────────────

PLACEHOLDERS = [
    # (nombre_archivo, tipo, label, color_extra)
    # Armazones — PNG transparente para VTO
    ("armazon-wayfarer-clasico.png",  "armazon", "Ray-Ban — Wayfarer Clásico",  (25,  25,  25)),
    ("armazon-holbrook.png",          "armazon", "Oakley — Holbrook",           (30,  40,  80)),
    ("armazon-prada-pr01os.png",      "armazon", "Prada — PR 01OS",             (20,  20,  20)),
    ("armazon-tomford-ft5634b.png",   "armazon", "Tom Ford — FT5634-B",         (60,  30,   0)),
    ("armazon-carrera-205v4.png",     "armazon", "Carrera — 205/V/4-F 55",      (10,  60,  90)),
    # Cristales — fondo azul claro
    ("cristal-essilor-varilux.png",   "cristal", "Essilor — Varilux X Series",  (60, 120, 200)),
    ("cristal-zeiss-individual2.png", "cristal", "Zeiss — Individual 2",        (40, 100, 180)),
    ("cristal-hoya-idmystyle.png",    "cristal", "Hoya — ID MyStyle V+",        (50, 110, 190)),
    ("cristal-nikon-seemax.png",      "cristal", "Nikon — SeeMax Ultimate",     (30,  90, 170)),
    ("cristal-shamir-autograph3.png", "cristal", "Shamir — Autograph III",      (70, 130, 210)),
    # Lentes de contacto — fondo verde agua
    ("lente-acuvue-oasys.png",        "lente",   "Acuvue — Oasys 1-Day",        (40, 160, 140)),
    ("lente-bausch-ultra.png",        "lente",   "Bausch+Lomb — Ultra",         (50, 140, 120)),
    ("lente-cooper-biofinity.png",    "lente",   "CooperVision — Biofinity",    (30, 150, 130)),
    ("lente-alcon-dailies.png",       "lente",   "Alcon — Dailies Total1",      (60, 170, 150)),
    ("lente-cooper-proclear.png",     "lente",   "CooperVision — Proclear",     (20, 130, 110)),
]


def generar_placeholder_png(nombre_archivo: str) -> None:
    """Genera el placeholder para un producto por nombre de archivo."""
    for nombre, tipo, label, color in PLACEHOLDERS:
        if nombre == nombre_archivo:
            if tipo == "armazon":
                _armazon_png(nombre, label, color_frame=color)
            else:
                _producto_png(nombre, label, color_acento=color)
            return
    # Si no está en la tabla, generar uno genérico
    label = nombre_archivo.replace(".png", "").replace("-", " ").title()
    _producto_png(nombre_archivo, label)


def generar_todos() -> None:
    print(f"Destino: {SALIDA_DIR}\n")
    for nombre, tipo, label, color in PLACEHOLDERS:
        destino = SALIDA_DIR / nombre
        if destino.exists():
            print(f"  [skip] {nombre} ya existe")
            continue
        if tipo == "armazon":
            _armazon_png(nombre, label, color_frame=color)
        else:
            _producto_png(nombre, label, color_acento=color)
    print(f"\n✓ {len(PLACEHOLDERS)} placeholders listos en static/productos/")


if __name__ == "__main__":
    generar_todos()
