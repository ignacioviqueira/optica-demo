# CLAUDE.md — Contexto del proyecto

> Colocá este archivo en la raíz del repositorio del demo. Claude Code lo lee
> automáticamente al inicio de cada sesión. Mantenelo actualizado a medida que
> el proyecto crece (podés correr `/init` para que Claude Code lo regenere).

## Qué estamos construyendo

**Prototipo / demo** del *Sistema Web de Gestión Comercial y Prueba Virtual para
Ópticas* — Trabajo Final de Graduación (Universidad Siglo 21, Ingeniería en
Software, Ignacio Federico Viqueira).

El sistema digitaliza una óptica minorista: catálogo e-commerce, **prueba virtual
fotográfica (Virtual Try-On / VTO)** de armazones, gestión de inventario,
procesamiento de pedidos con validación humana de recetas, y un panel analítico
gerencial.

**El VTO es el diferenciador del proyecto** (prioridad "Muy Alta" en el backlog).
Debe ser la estrella del demo.

## Naturaleza del demo: "simulación funcional sobre el stack real"

No es un sistema de producción. Es un prototipo **demostrable y descargable** que
recorre el flujo completo end-to-end con datos sembrados.

- **REAL (implementado de verdad):** autenticación + roles, CRUD de inventario,
  catálogo con filtros, **VTO con OpenCV.js**, carrito, creación de pedidos,
  máquina de estados del pedido, carga/visualización de recetas, dashboard con
  gráficos.
- **SIMULADO / MOCKEADO:** pasarela de pago (pantalla "aprobado" ficticia, sin
  cobro real), envío de emails (se loguea o se dispara un flujo n8n de mentira),
  alertas por tiempo. No implementar integraciones de pago/email reales.
- **SEMBRADO (seed):** productos, categorías, un usuario por rol, recetas y
  pedidos de ejemplo, para que el dashboard y los listados tengan datos desde el
  primer arranque.

Regla práctica: si una feature no se ve en el recorrido del video demo, no la
construyas todavía.

## Stack (exacto, según la tesis — no cambiar sin avisar)

- **Backend / Capa de Negocio:** Django (Python), expone una API REST.
- **Base de datos / Capa de Datos:** PostgreSQL.
- **Frontend / Capa de Presentación:** HTML / CSS / JS servido por Django.
- **VTO:** OpenCV.js (visión por computadora en el navegador, lado cliente).
- **Capa de Integración:** n8n (orquestación de flujos automatizados).
- **Orquestación:** Docker + docker-compose (servicios: `web`, `db`, `n8n`).

## Arquitectura (4 capas)

1. **Presentación** — Navegador web. Interfaz HTML/CSS/JS + módulo VTO (OpenCV.js)
   procesando imágenes del lado del cliente.
2. **Negocio** — Servidor Django con API REST (Python): lógica de inventario,
   autenticación, pedidos, analítica.
3. **Integración** — n8n orquesta flujos automatizados (ej. nuevo pedido →
   notificación; stock crítico → alerta).
4. **Datos** — PostgreSQL: persistencia transaccional.

## Modelo de datos (6 entidades)

- **USUARIO**: id_usuario, correo_electronico (identificador único), contraseña,
  nombre, rol.
- **CATEGORIA**: id_categoria, nombre, descripcion.
- **PRODUCTO**: id_producto, nombre, marca, precio, stock_actual, stock_minimo,
  id_categoria (FK).
- **RECETA**: id_receta, id_usuario (FK), esfera_od, cilindro_od, eje_od, dnp,
  fecha_emision.
- **PEDIDO**: id_pedido, id_usuario (FK), fecha, total, estado.
- **DETALLE_PEDIDO**: id_detalle, id_pedido (FK), id_producto (FK), cantidad,
  precio_unitario.

> En Django conviene un `CustomUser` (o `User` + perfil) con campo `rol`. Mantené
> los nombres de entidad/campo coherentes con el diagrama entidad-relación de la
> tesis para que el demo sea defendible.

## Roles y permisos

- **Cliente:** catálogo, VTO, carrito, su propio historial de recetas. Login redirige al catálogo.
- **Ventas / Empleada:** audita y valida pedidos, ve recetas adjuntas, actualiza estado de órdenes. No modifica inventario ni ve métricas gerenciales. Login redirige al panel operativo.
- **Gerencia / Dueña:** acceso total. CRUD de inventario, alta/baja de empleados, dashboard analítico. Login redirige al dashboard.

## Seguridad (según la tesis — respetar)

- Correo electrónico como identificador único.
- Contraseña: mínimo 8 caracteres, con mayúscula, minúscula, número y al menos un
  carácter especial.
- Bloqueo temporal de cuenta tras 5 intentos fallidos.
- Contraseñas con **PBKDF2 + SHA-256** (es el hasher por defecto de Django — ya
  cumple).
- Transmisión bajo HTTPS/SSL (en el demo local basta HTTP; documentarlo).

## Máquina de estados del pedido

`Confirmado - Pendiente de Validación` → (Ventas valida) → `En Proceso de Armado`
→ (Gerencia termina armado) → `Listo para Entrega`.
Rama de rechazo: Ventas rechaza con motivo → `Rechazado` (+ email simulado al cliente).

## Pantallas a replicar (hay prototipos en la tesis)

1. **Interfaz de Acceso** (login con email/contraseña, "Crear cuenta").
2. **Catálogo** (grilla de productos + filtros laterales: categoría, marca,
   material, forma, rango de precio; botón "Prueba Virtual" y "Añadir al Carrito"
   en cada tarjeta).
3. **Prueba Virtual** (rostro del usuario + armazón superpuesto a escala; botón
   "Añadir al Carrito" que registra el evento de conversión).
4. **Dashboard** (KPIs: ventas totales, pedidos, clientes nuevos, tasa de
   conversión; gráficos de ventas; uso del VTO; productos populares; alertas de
   stock; pedidos recientes; menú lateral).

## Historias de usuario (resumen del backlog)

- HU-01 Seguridad y acceso · HU-02 Inventario · HU-03 Carga/digitalización de recetas
- HU-04 Catálogo interactivo · HU-05 Búsqueda por filtros
- HU-06 Prueba virtual 2D · HU-07 Calibración de escala facial  ← **núcleo VTO**
- HU-08 Carrito · HU-09 Pasarela de pago (simulada) · HU-10 Auditoría de pedidos
- HU-11 Orden de trabajo técnica (PDF) · HU-12 Panel de KPIs · HU-13 Métricas VTO
- HU-14 Alertas de stock crítico · HU-15 Historial de compras

## Enfoque técnico del VTO (OpenCV.js)

1. Cargar OpenCV.js (WASM) en el navegador.
2. Entrada: foto subida por el usuario (JPG/PNG) **o** cámara web.
3. Detección con clasificadores Haar (`haarcascade_frontalface_default.xml` +
   `haarcascade_eye.xml`) → caja del rostro y posición de los ojos.
4. Calcular distancia inter-pupilar (escala), ángulo del eje ocular (rotación).
5. Superponer PNG transparente del armazón en un `<canvas>`, escalado al ancho del
   rostro y rotado al eje ocular.
6. Controles de ajuste manual (desplazamiento fino), según HU-07.
7. Al "Añadir al Carrito" desde el VTO, registrar un evento de conversión para las
   métricas del dashboard (HU-13).

> Haar alcanza para un overlay 2D sobre foto (cumple HU-06/07: escala por IPD +
> rotación por eje). Si se busca más precisión, usar el módulo `face` de OpenCV.js
> con modelo de landmarks LBF. Documentar la decisión.

## Convenciones

- Idioma del dominio en español (entidades, rutas de negocio); código y librerías
  en inglés según convención.
- Commits chicos, uno por fase del plan (ver el prompt inicial / la guía).
- Tests donde aporten: matemática de escala/rotación del VTO y máquina de estados
  del pedido (la tesis incluye "testing unitario" en el Sprint 2).
- Todo debe levantar con `docker compose up --build` sin pasos manuales extra
  (el seed corre automáticamente o con un comando documentado).

## Comandos (objetivo)

```bash
docker compose up --build      # levanta web + db + n8n
docker compose run web python manage.py migrate
docker compose run web python manage.py seed_demo   # carga datos de ejemplo
docker compose run web python manage.py test        # corre tests
```

URLs objetivo: app en `http://localhost:8000`, n8n en `http://localhost:5678`.
