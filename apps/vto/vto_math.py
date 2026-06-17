"""
Funciones matemáticas del VTO — implementadas en Python para testing unitario.
Las mismas fórmulas se replican en el frontend con JavaScript (ver templates/vto/index.html).

Decisión de diseño — Haar vs. LBF landmarks:
  Se eligió Haar (haarcascade_frontalface + haarcascade_eye) porque:
  - Funciona sin dependencias adicionales en OpenCV.js puro (no requiere el módulo 'face').
  - Suficiente para overlay 2D: escala por IPD + rotación por eje ocular (HU-06/07).
  - Latencia < 500 ms en imágenes de 800 px en un navegador moderno.
  Si se requiriera mayor precisión (landmarks precisos para gafas progresivas o caras
  de perfil) se reemplazaría por el detector LBF del módulo cv.face — ver vto.md.
"""
import math


def calcular_ancho_frame(ipd_px: float, frame_mm: float = 140.0, ipd_mm: float = 63.0) -> float:
    """
    Ancho del armazón en píxeles dado el IPD medido en la imagen.

    La escala px/mm se deriva del IPD observado.
    Armazón estándar ≈ 140 mm; IPD promedio ≈ 63 mm → ratio ≈ 2.22.

    Args:
        ipd_px:   Distancia inter-pupilar en píxeles (medida en la imagen).
        frame_mm: Ancho real del armazón en mm (default 140).
        ipd_mm:   IPD de referencia en mm (default 63, promedio adulto).

    Returns:
        Ancho del armazón en píxeles.

    Raises:
        ValueError: Si ipd_px ≤ 0.
    """
    if ipd_px <= 0:
        raise ValueError("ipd_px debe ser positivo")
    return ipd_px * (frame_mm / ipd_mm)


def calcular_angulo_ocular(left_x: float, left_y: float,
                            right_x: float, right_y: float) -> float:
    """
    Ángulo (radianes) del eje que une los centros oculares.

    Positivo = inclinación horaria (ojo derecho más bajo).
    Negativo = inclinación antihoraria (ojo derecho más alto).
    Cero = ojos al mismo nivel.

    Args:
        left_x, left_y:   Centro del ojo izquierdo (en imagen, lado izquierdo de la foto).
        right_x, right_y: Centro del ojo derecho (en imagen, lado derecho de la foto).

    Returns:
        Ángulo en radianes, rango (-π, π].
    """
    return math.atan2(right_y - left_y, right_x - left_x)


def calcular_ipd_px(left_x: float, left_y: float,
                     right_x: float, right_y: float) -> float:
    """Distancia euclídea entre centros oculares en píxeles."""
    return math.hypot(right_x - left_x, right_y - left_y)
