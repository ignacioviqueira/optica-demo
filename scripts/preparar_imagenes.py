"""
scripts/preparar_imagenes.py
Pipeline de preparación de imágenes de productos (UN SOLO USO — no runtime).

Requisitos locales (no van al contenedor Docker):
    pip install rembg pillow requests

Uso:
    # Procesar todas las fuentes en assets/fuentes/ y las URLs del dict FUENTES_URL
    python scripts/preparar_imagenes.py

    # Solo procesar un archivo específico
    python scripts/preparar_imagenes.py --solo assets/fuentes/mi_armazon.jpg

    # Solo generar placeholders sin rembg
    python scripts/preparar_imagenes.py --solo-placeholders

El pipeline:
1. Descarga las imágenes declaradas en FUENTES_URL (si no existen en assets/fuentes/).
2. Combina con cualquier imagen que el usuario haya soltado en assets/fuentes/.
3. Pasa TODAS por rembg para remover el fondo → PNG con alpha.
4. Recorta al bounding box del objeto, centra y normaliza a ANCHO_SALIDA px.
5. Guarda en static/productos/ con el nombre definido en FUENTES_URL.
6. Genera placeholders vectoriales para cualquier producto sin imagen.
"""

import argparse
import io
import os
import sys
from pathlib import Path

# ── Rutas base ────────────────────────────────────────────────────────────────
REPO_ROOT     = Path(__file__).resolve().parent.parent
FUENTES_DIR   = REPO_ROOT / "assets" / "fuentes"
SALIDA_DIR    = REPO_ROOT / "static" / "productos"
ANCHO_SALIDA  = 600   # px, ancho normalizado de la salida

FUENTES_DIR.mkdir(parents=True, exist_ok=True)
SALIDA_DIR.mkdir(parents=True, exist_ok=True)

# ── Fuentes de imagen por producto ────────────────────────────────────────────
# Formato: nombre_salida → URL de imagen libre de derechos (CC0/MIT/Pexels/Unsplash/Wikimedia).
# Las imágenes se descargan una sola vez a assets/fuentes/.
# Cambiar la URL si el enlace expira — buscá "eyeglasses front view" o el nombre de montura.
FUENTES_URL = {
    # Armazones (necesitan fondo transparente para VTO)
    "armazon-wayfarer-clasico.png": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/"
        "Ray-Ban_Wayfarer.jpg/640px-Ray-Ban_Wayfarer.jpg"
    ),
    "armazon-holbrook.png": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/"
        "Oakley_Holbrook_sunglasses.jpg/640px-Oakley_Holbrook_sunglasses.jpg"
    ),
    "armazon-prada-pr01os.png": (
        "https://images.unsplash.com/photo-1572635196237-14b3f281503f"
        "?w=640&q=80"
    ),
    "armazon-tomford-ft5634b.png": (
        "https://images.unsplash.com/photo-1511499767150-a48a237f0083"
        "?w=640&q=80"
    ),
    "armazon-carrera-205v4.png": (
        "https://images.unsplash.com/photo-1559581015-b3e2c63f0b73"
        "?w=640&q=80"
    ),
    # Cristales (imagen de caja/producto — no necesitan fondo transparente)
    "cristal-essilor-varilux.png": (
        "https://images.unsplash.com/photo-1508296695146-257a814070b4"
        "?w=640&q=80"
    ),
    "cristal-zeiss-individual2.png": (
        "https://images.unsplash.com/photo-1516534775068-ba3e7458af70"
        "?w=640&q=80"
    ),
    "cristal-hoya-idmystyle.png": (
        "https://images.unsplash.com/photo-1576602976047-174e57a47881"
        "?w=640&q=80"
    ),
    "cristal-nikon-seemax.png": (
        "https://images.unsplash.com/photo-1574258495973-f010dfbb5371"
        "?w=640&q=80"
    ),
    "cristal-shamir-autograph3.png": (
        "https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d"
        "?w=640&q=80"
    ),
    # Lentes de contacto (imagen de caja/blíster)
    "lente-acuvue-oasys.png": (
        "https://images.unsplash.com/photo-1583394293214-0f8a7bea58ac"
        "?w=640&q=80"
    ),
    "lente-bausch-ultra.png": (
        "https://images.unsplash.com/photo-1577982787983-e07c6730f2d3"
        "?w=640&q=80"
    ),
    "lente-cooper-biofinity.png": (
        "https://images.unsplash.com/photo-1560343787-8f85eed5cc7b"
        "?w=640&q=80"
    ),
    "lente-alcon-dailies.png": (
        "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa"
        "?w=640&q=80"
    ),
    "lente-cooper-proclear.png": (
        "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7"
        "?w=640&q=80"
    ),
}

# Armazones: requieren transparencia para el overlay VTO
NOMBRES_ARMAZON = {k for k in FUENTES_URL if k.startswith("armazon-")}


def descargar(nombre: str, url: str) -> Path:
    destino = FUENTES_DIR / nombre
    if destino.exists():
        print(f"  [cache] {nombre}")
        return destino
    print(f"  [descarga] {nombre} ← {url[:60]}…")
    import requests  # noqa: PLC0415
    resp = requests.get(url, timeout=30, headers={"User-Agent": "optica-demo-script/1.0"})
    resp.raise_for_status()
    destino.write_bytes(resp.content)
    return destino


def remover_fondo(src: Path) -> bytes:
    from rembg import remove  # noqa: PLC0415
    data = src.read_bytes()
    return remove(data)


def normalizar(png_bytes: bytes, es_armazon: bool) -> bytes:
    from PIL import Image  # noqa: PLC0415

    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")

    if es_armazon:
        # Recortar al bounding box del objeto (canal alpha)
        r, g, b, a = img.split()
        bbox = a.getbbox()
        if bbox:
            img = img.crop(bbox)
        # Normalizar ancho
        w, h = img.size
        nuevo_h = int(h * ANCHO_SALIDA / w)
        img = img.resize((ANCHO_SALIDA, nuevo_h), Image.LANCZOS)
    else:
        # Para no-armazones: convertir a RGB con fondo blanco y escalar
        fondo = Image.new("RGBA", img.size, (255, 255, 255, 255))
        fondo.paste(img, mask=img.split()[3])
        img = fondo.convert("RGB")
        w, h = img.size
        nuevo_h = int(h * ANCHO_SALIDA / w)
        img = img.resize((ANCHO_SALIDA, nuevo_h), Image.LANCZOS)

    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    return out.getvalue()


def procesar_archivo(src: Path, nombre_salida: str) -> None:
    es_armazon = nombre_salida in NOMBRES_ARMAZON
    print(f"  [rembg] {nombre_salida} ({'armazón' if es_armazon else 'producto'})")
    try:
        sin_fondo = remover_fondo(src)
        resultado = normalizar(sin_fondo, es_armazon)
        destino = SALIDA_DIR / nombre_salida
        destino.write_bytes(resultado)
        print(f"  [ok] → {destino.relative_to(REPO_ROOT)}")
    except Exception as exc:
        print(f"  [error] {nombre_salida}: {exc}")
        print(f"  [fallback] Generando placeholder para {nombre_salida}…")
        from scripts.generar_placeholders import generar_placeholder_png  # noqa: PLC0415
        generar_placeholder_png(nombre_salida)


def main(args=None):
    parser = argparse.ArgumentParser(description="Pipeline de preparación de imágenes")
    parser.add_argument("--solo", help="Procesar solo un archivo fuente específico")
    parser.add_argument("--solo-placeholders", action="store_true",
                        help="Solo generar placeholders sin rembg")
    ns = parser.parse_args(args)

    if ns.solo_placeholders:
        print("Generando placeholders…")
        sys.path.insert(0, str(REPO_ROOT))
        from scripts.generar_placeholders import generar_todos  # noqa: PLC0415
        generar_todos()
        return

    print(f"\nFuentes: {FUENTES_DIR}")
    print(f"Salida:  {SALIDA_DIR}\n")

    if ns.solo:
        src = Path(ns.solo)
        nombre = src.name.rsplit(".", 1)[0] + ".png"
        procesar_archivo(src, nombre)
        return

    # 1. Descargar fuentes declaradas
    print("── Descargando fuentes ──────────────────────────────────────────────")
    for nombre, url in FUENTES_URL.items():
        src_nombre = nombre.rsplit(".", 1)[0] + Path(url.split("?")[0]).suffix
        descargar(src_nombre, url)

    # 2. Procesar cada fuente → salida
    print("\n── Procesando imágenes ──────────────────────────────────────────────")
    for nombre_salida, url in FUENTES_URL.items():
        ext_src = Path(url.split("?")[0]).suffix or ".jpg"
        src_nombre = nombre_salida.rsplit(".", 1)[0] + ext_src
        src = FUENTES_DIR / src_nombre
        if src.exists():
            procesar_archivo(src, nombre_salida)
        else:
            print(f"  [faltante] {src} — generando placeholder")
            sys.path.insert(0, str(REPO_ROOT))
            from scripts.generar_placeholders import generar_placeholder_png  # noqa: PLC0415
            generar_placeholder_png(nombre_salida)

    # 3. Procesar cualquier archivo extra que el usuario haya soltado en assets/fuentes/
    procesados = {
        (nombre_salida.rsplit(".", 1)[0] + Path(url.split("?")[0]).suffix)
        for nombre_salida, url in FUENTES_URL.items()
    }
    extras = [f for f in FUENTES_DIR.iterdir()
              if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
              and f.name not in procesados]
    if extras:
        print("\n── Archivos extra en assets/fuentes/ ────────────────────────────────")
        for src in extras:
            nombre_salida = src.stem + ".png"
            procesar_archivo(src, nombre_salida)

    print("\n✓ Pipeline completado")


if __name__ == "__main__":
    main()
