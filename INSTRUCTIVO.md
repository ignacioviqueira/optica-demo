# INSTRUCTIVO — Puesta en marcha del demo

> **Para el evaluador / tribunal:** este documento describe cómo levantar el
> sistema desde cero y qué recorrido seguir para ver todas las funcionalidades.

---

## Prerrequisitos

| Herramienta | Versión mínima |
|---|---|
| Docker Desktop | 24+ |
| Docker Compose (plugin) | v2.20+ |
| Navegador web moderno | Chrome / Firefox / Edge |

> En Linux: `docker compose` (sin guión). En Mac/Windows: Docker Desktop ya lo incluye.

---

## Levantar el stack (una sola vez)

```bash
# 1. Descomprimir / clonar el repositorio
git clone <repo-url> optica-demo
cd optica-demo

# 2. Copiar variables de entorno (valores por defecto son suficientes para el demo)
cp .env.example .env

# 3. Levantar todo (build + migrate + seed se ejecutan automáticamente)
docker compose up --build
```

El arranque tarda ~2 minutos la primera vez (descarga de imágenes + build).
Cuando veas `[entrypoint] Iniciando servidor...` el sistema está listo.

- **Aplicación:** http://localhost:8000  
- **n8n:** http://localhost:5678  
- **Admin Django:** http://localhost:8000/admin

> El comando `seed_demo` es **idempotente**: podés correrlo más de una vez sin
> duplicar datos. Si necesitás reiniciar los datos, bajá el stack con
> `docker compose down -v` y volvé a levantarlo.

---

## Importar los flujos de n8n (opcional para el demo de integración)

> **Sin este paso los webhooks de notificación devuelven 404**, pero el resto
> del sistema funciona con normalidad.

1. Abrir **http://localhost:5678**
2. Ir a **Workflows → Add workflow → Import from file**
3. Importar `integracion/n8n/pedido_validado.json`
4. Importar `integracion/n8n/stock_critico.json`

Los JSON ya incluyen `"active": true`; n8n los activa al importar.
Si el toggle aparece en **Off**, activarlo manualmente.

Verificar que los webhooks responden:

```bash
curl -X POST http://localhost:5678/webhook/pedido-validado \
  -H "Content-Type: application/json" \
  -d '{"pedido_id":1,"usuario_email":"test@demo.com","total":"25000","estado":"En Proceso de Armado","usuario_nombre":"Test"}'
```

---

## Credenciales de demo

| Rol | Email | Contraseña | Acceso a |
|---|---|---|---|
| **Gerencia** | `gerencia@optica.demo` | `Gerencia@123` | Todo: dashboard, inventario, pedidos, catálogo |
| **Ventas** | `ventas@optica.demo` | `Ventas@123` | Pedidos (validar/rechazar), catálogo |
| **Cliente** | `cliente@optica.demo` | `Cliente@123` | Catálogo, VTO, carrito, mis pedidos |

> La cuenta de Gerencia también tiene acceso al **Admin Django**
> (`http://localhost:8000/admin`).

---

## Recorrido sugerido para el video / demo

### Paso 1 — Landing y login (30 seg)
- Abrir http://localhost:8000
- Mostrar la tabla de credenciales y el recorrido guiado
- Hacer clic en **"Ingresar como Cliente"**

### Paso 2 — Catálogo y filtros (1 min)
- Explorar la grilla de productos
- Usar filtros laterales: categoría **Armazones**, marca **Ray-Ban**
- Mostrar que el resultado se actualiza dinámicamente

### Paso 3 — Prueba Virtual VTO (2 min) ← **punto fuerte del demo**
- Desde la tarjeta de un armazón, hacer clic en **"Prueba Virtual"**
- Esperar que el badge pase de *Cargando OpenCV…* a **Listo** (~5-10 seg)
- Subir una foto con una cara visible (o usar la cámara web)
- Mostrar el overlay del armazón superpuesto al rostro
- Usar los controles de ajuste fino (desplazamiento, zoom)
- Hacer clic en **"Añadir al Carrito"** — esto registra un evento de conversión

### Paso 4 — Carrito y checkout (1 min)
- Abrir el carrito (ícono en la navbar)
- Hacer clic en **Confirmar pedido**
- Pasar por el pago simulado → comprobante generado

### Paso 5 — Panel operativo de Ventas (1 min)
- Cerrar sesión e ingresar como **Ventas**
- Ir a **Pedidos** — ver el pedido recién creado en estado *Pendiente de Validación*
- Validar el pedido → estado cambia a *En Proceso de Armado*
- (Opcional) Rechazar otro pedido con un motivo

### Paso 6 — Dashboard Gerencial (2 min)
- Ingresar como **Gerencia**
- Abrir **Dashboard**
- Mostrar los 4 KPIs (ventas, pedidos, clientes nuevos, tasa de conversión VTO)
- Cambiar el filtro de período: Hoy / Semana / Mes / Todo
- Mostrar los 3 gráficos (ventas diarias, productos más vendidos, VTO)
- Señalar la tabla de stock crítico con los 5 productos en alerta
- Hacer clic en **Exportar CSV** y abrir el archivo

### Paso 7 — Inventario (30 seg)
- Ir a **Inventario**
- Crear un producto nuevo o editar uno existente
- Mostrar que el stock mínimo genera alerta en el dashboard

### Paso 8 — Integración n8n (1 min) *(si los flujos fueron importados)*
- Abrir http://localhost:5678 en otra pestaña
- Volver a validar un pedido desde el panel de Ventas
- Mostrar en n8n **Executions** que el flujo `pedido_validado` se ejecutó
- Ver el log de la "notificación simulada"

---

## Correr los tests

```bash
docker compose run --rm web python manage.py test
```

Resultado esperado: **163 tests, 0 failures**.

---

## Detener y limpiar

```bash
# Solo detener (mantiene datos)
docker compose down

# Detener y borrar volúmenes (resetea la base de datos)
docker compose down -v
```

---

## Limitaciones conocidas del prototipo

| Limitación | Detalle |
|---|---|
| **Pago simulado** | No hay integración real con pasarela de pago (Mercado Pago, Stripe, etc.). La pantalla de "pago aprobado" es ficticia. |
| **Email simulado** | Los emails se loguean en stdout del contenedor (`EMAIL_BACKEND = console`) o disparan un flujo n8n de demo. No se envían correos reales. |
| **VTO 2D** | La superposición es 2D (foto estática o cámara). No hay renderizado 3D ni tracking en tiempo real con rotación de cabeza. |
| **HTTPS** | El demo corre en HTTP local. En producción se requeriría HTTPS/SSL. |
| **Multiusuario concurrent** | No se testeó bajo carga concurrente. Es un prototipo monoinstancia. |
| **Admin Django expuesto** | El admin está habilitado en modo demo para facilitar la inspección de datos. En producción requeriría restricción de acceso. |
