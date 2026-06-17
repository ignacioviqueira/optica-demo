# Módulo VTO — Prueba Virtual (Virtual Try-On)

> Documentación técnica del módulo VTO para el Trabajo Final de Graduación.
> Universidad Siglo 21 — Ingeniería en Software — Ignacio Federico Viqueira.

---

## Qué hace

El módulo VTO permite al usuario **superponer un armazón virtual sobre su propia
foto** (o captura de cámara web) para evaluar cómo le quedaría antes de comprarlo.
El overlay se escala al tamaño real en base a la distancia inter-pupilar (IPD)
medida automáticamente con visión por computadora, y se rota para alinearse con
el eje ocular.

Cubre las historias de usuario HU-06 (superposición 2D), HU-07 (calibración por
IPD y eje), y HU-13 (registro de conversión para métricas del dashboard).

---

## Tecnología central: OpenCV.js

OpenCV.js es la compilación a WebAssembly de la librería OpenCV, ejecutada
completamente en el navegador del usuario (sin enviar imágenes al servidor).

```
Foto/webcam → <canvas> → OpenCV.js WASM → detección → overlay 2D → <canvas>
```

**Ventajas**:
- Sin costo de red — la imagen no sale del dispositivo del usuario.
- Sin servidor de GPU — cero infraestructura adicional.
- Funciona en cualquier navegador moderno.

**Sin dependencia de red en runtime**: `opencv.js` (~10.7 MB) se sirve desde
`static/vto/opencv.js`, incluido en el repositorio. No se requiere conexión a internet
para usar el VTO. El CDN `docs.opencv.org/4.x/opencv.js` actúa solo como red de
seguridad en el `onerror` del script, por si el archivo estático local fallara.

---

## Decisión de diseño: Haar vs. LBF landmarks

### Opción A — Haar cascades (implementada)

Se usan dos clasificadores Haar preentrenados:
- `haarcascade_frontalface_default.xml` — detecta el rectángulo del rostro.
- `haarcascade_eye.xml` — detecta los ojos dentro de la región del rostro.

**Por qué se eligió Haar:**
1. Disponible en OpenCV.js puro, sin dependencias adicionales del módulo `face`.
2. Los XML (~1.2 MB combinados) se sirven desde `static/vto/cascades/` sin
   necesidad de descargas externas en runtime.
3. Suficiente para un overlay 2D: la IPD y el ángulo del eje ocular se derivan
   de los centros de los dos rectángulos de ojo, que Haar detecta con buena
   precisión en condiciones de iluminación normal y vista frontal.
4. Latencia < 600 ms en imágenes de 800 × 600 px en hardware de gama media.

**Cuándo Haar falla:**
- Ángulos de cabeza > 25°.
- Oclusiones (cabello sobre ojos, gafas de sol oscuras).
- Iluminación muy lateral o contraluces.

### Opción B — LBF landmarks del módulo `cv.face` (no implementada)

El submódulo `face` de OpenCV incluye el detector de 68 landmarks faciales basado
en Local Binary Feature (LBF). Proporciona posiciones precisas de cada esquina
ocular, lo que permitiría calcular la IPD con mayor exactitud y manejar cabezas
ligeramente giradas.

**Por qué no se implementó:**
- Requiere el binario `face_landmark_model.dat` (~54 MB) descargado por separado.
- El módulo `cv.face` no viene compilado en la distribución estándar de OpenCV.js
  de `docs.opencv.org`; habría que compilar OpenCV.js con `-DOPENCV_EXTRA_MODULES_PATH`.
- Para el objetivo del demo (overlay 2D en foto frontal), Haar es suficiente.

**Cómo migrar a LBF si se necesitara:**
```javascript
// Reemplazar _detectar() por:
const lbf = new cv.face.createFacemarkLBF();
lbf.loadModel('/static/vto/models/lbfmodel.yaml');
const faces = detectFacesHaar(gray);
const landmarks = new cv.face.vectorLandmarks();
lbf.fit(gray, faces, landmarks);
const pts = landmarks.get(0);
// left eye center = media de landmarks 36-41
// right eye center = media de landmarks 42-47
```

---

## Matemática de escala y rotación

Las funciones están implementadas en Python (`apps/vto/vto_math.py`) y
replicadas en JavaScript (`templates/vto/index.html`) para que sean
**testables con `manage.py test`**.

### Escala (IPD → ancho del armazón en píxeles)

```
ancho_frame_px = ipd_px × (frame_real_mm / ipd_real_mm)
```

Valores de referencia:
- `frame_real_mm = 140` (armazón adulto estándar).
- `ipd_real_mm = 63` (IPD promedio adulto).
- Ratio resultante ≈ **2.22×** el IPD medido.

### Rotación (eje ocular)

```
ángulo_rad = atan2(ojo_derecho.y − ojo_izquierdo.y,
                    ojo_derecho.x − ojo_izquierdo.x)
```

El canvas 2D se rota en ese ángulo antes de dibujar el PNG del armazón.

### Posición del centro del armazón

```
centro_x = (ojo_izquierdo.x + ojo_derecho.x) / 2  + ajuste_x
centro_y = (ojo_izquierdo.y + ojo_derecho.y) / 2  + ajuste_y
```

Los controles de ajuste fino (sliders X, Y, escala) permiten al usuario corregir
pequeñas imprecisiones de la detección (HU-07).

---

## Flujo de la UI

```
[Carga OpenCV.js (async)]
         ↓
[Carga cascade XMLs desde /static/ vía fetch]
         ↓
     Usuario sube foto / captura webcam
         ↓
[Dibuja imagen en <canvas>]  →  [cv.imread(canvas) → detección Haar]
         ↓
  calibración = { leftEye, rightEye, ipd, angle }
         ↓
    renderAll():
      ctx.drawImage(baseImg)           ← imagen original
      ctx.drawImage(frameImg, cx, cy)  ← PNG armazón rotado y escalado
         ↓
  Usuario ajusta sliders → renderAll() se ejecuta en tiempo real
         ↓
  Usuario hace clic "Añadir al carrito"
    → POST /api/vto/evento/ { producto_id }  ← registra conversión (HU-13)
    → localStorage["carrito"] actualizado
    → badge del carrito actualizado
```

---

## Archivos del módulo

| Ruta | Descripción |
|------|-------------|
| `apps/vto/models.py` | Modelo `EventoVTO` (HU-13) |
| `apps/vto/vto_math.py` | Funciones Python de escala y rotación (testables) |
| `apps/vto/views.py` | Vista HTML + API `RegistrarEventoVTOView` |
| `apps/vto/urls.py` | Rutas HTML (`/vto/`) |
| `apps/vto/api_urls.py` | Rutas API (`/api/vto/`) |
| `apps/vto/tests.py` | Tests unitarios + integración |
| `apps/vto/management/commands/generate_vto_frames.py` | Genera PNG de armazones |
| `templates/vto/index.html` | Pantalla VTO completa |
| `static/vto/cascades/haarcascade_frontalface_default.xml` | Clasificador Haar (rostro) |
| `static/vto/cascades/haarcascade_eye.xml` | Clasificador Haar (ojos) |
| `static/vto/frames/*.png` | PNGs de armazones con fondo transparente |
| `static/vto/opencv.js` | OpenCV.js 4.x (~10.7 MB) servido localmente |

---

## Setup inicial

```bash
# 1. Levantar servicios
docker compose up --build

# 2. Migrar
docker compose run web python manage.py migrate

# 3. Cargar datos de ejemplo
docker compose run web python manage.py seed_demo

# 4. Generar PNGs de armazones
docker compose run web python manage.py generate_vto_frames
```

Todos los archivos estáticos del VTO están incluidos en el repositorio:
- `static/vto/cascades/` — clasificadores Haar XML
- `static/vto/opencv.js` — OpenCV.js 4.x (~10.7 MB)
- `static/vto/frames/` — PNGs de armazones (generados por `generate_vto_frames`)

No se requieren descargas adicionales después de clonar el repositorio.

---

## Nota sobre la versión de OpenCV.js

El archivo `static/vto/opencv.js` corresponde a la build `4.x` descargada desde
`https://docs.opencv.org/4.x/opencv.js`. La URL `4.10.0` ya no está disponible
en el CDN de OpenCV. El fallback en el `onerror` del `<script>` apunta a `4.x`.

---

## Tests

```bash
docker compose run web python manage.py test apps.vto
```

Cobertura de tests:

| Test | Qué verifica |
|------|-------------|
| `EscalaVTOTest` | `calcular_ancho_frame()` — proporcionalidad, errores |
| `AnguloOcularVTOTest` | `calcular_angulo_ocular()` — signos, casos límite |
| `IPDCalculoTest` | `calcular_ipd_px()` — Pitágoras, simetría |
| `EventoVTOModelTest` | Creación, `__str__`, ordenamiento |
| `EventoVTOAPITest` | POST 201, 400, 403, 404 |
| `VTOViewTest` | Acceso, producto pre-cargado, 404 |
