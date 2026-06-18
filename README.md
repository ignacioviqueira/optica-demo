# Sistema de Gestión Óptica — Demo

Prototipo del **Sistema Web de Gestión Comercial y Prueba Virtual para Ópticas**.  
Trabajo Final de Graduación · Universidad Siglo 21 · Ignacio Federico Viqueira.

> Ver [INSTRUCTIVO.md](INSTRUCTIVO.md) para el recorrido detallado del demo y las
> instrucciones de puesta en marcha para el evaluador.

## Levantar el proyecto

```bash
# 1. Clonar y entrar al directorio
git clone <repo-url> optica-demo && cd optica-demo

# 2. Copiar variables de entorno (valores por defecto son suficientes)
cp .env.example .env

# 3. Levantar stack completo — migraciones y seed corren automáticamente
docker compose up --build
```

El sistema está listo cuando aparece `[entrypoint] Iniciando servidor...`
(~2 min la primera vez por descarga de imágenes).

### Comandos adicionales

```bash
# Correr tests
docker compose run --rm web python manage.py test

# Recargar datos de demo (idempotente)
docker compose run --rm web python manage.py seed_demo

# Resetear base de datos completa
docker compose down -v && docker compose up --build
```

## URLs

| Servicio | URL |
|----------|-----|
| Aplicación | http://localhost:8000 |
| Admin Django | http://localhost:8000/admin |
| n8n | http://localhost:5678 |

## Credenciales de demo

| Rol | Email | Contraseña |
|-----|-------|------------|
| Gerencia | `gerencia@optica.demo` | `Gerencia@123` |
| Ventas | `ventas@optica.demo` | `Ventas@123` |
| Cliente | `cliente@optica.demo` | `Cliente@123` |

> La cuenta de Gerencia tiene `is_staff=True` para acceder al admin de Django.

## Datos sembrados

El comando `seed_demo` (que corre automáticamente al levantar) carga:

- **3 usuarios** (uno por rol)
- **3 categorías**: Armazones, Cristales, Lentes de Contacto
- **15 productos** (5 por categoría), con 5 en stock crítico
- **3 recetas** para la usuaria cliente (fechas 2023–2025)
- **5 pedidos** en distintos estados:
  - 1 × Pendiente de Validación
  - 1 × En Proceso de Armado
  - 2 × Listo para Entrega
  - 1 × Rechazado (con motivo)

El seed es **idempotente**: ejecutarlo más de una vez no duplica registros.

## Flujos de integración n8n

Después de `docker compose up --build`, importar los flujos para que las
notificaciones funcionen:

1. Abrir **http://localhost:5678**
2. Ir a **Workflows → Add workflow → Import from file**
3. Importar `integracion/n8n/pedido_validado.json`
4. Importar `integracion/n8n/stock_critico.json`

> Los archivos JSON ya vienen con `"active": true`. n8n los activa al importar.
> Si el toggle queda en Off, activarlo manualmente desde la UI.
>
> Ver [docs/integracion.md](docs/integracion.md) para más detalles y cómo
> probar con `curl`.

## Funcionalidades implementadas

| Módulo | Descripción | HU |
|--------|-------------|-----|
| Autenticación | Login/registro con roles, bloqueo por intentos fallidos | HU-01 |
| Inventario | CRUD de productos y categorías, stock mínimo | HU-02 |
| Recetas | Adjunto de imagen de receta en checkout; visualización en panel operativo y PDF | HU-03 |
| Catálogo | Grilla con filtros (marca, categoría, precio, forma, material) | HU-04, HU-05 |
| **Prueba Virtual (VTO)** | OpenCV.js: detección facial Haar, overlay de armazón, calibración IPD | HU-06, HU-07 |
| Carrito | Gestión local con localStorage, badge animado | HU-08 |
| Checkout / Pago simulado | Creación de pedido, descuento de stock, comprobante | HU-09 |
| Pedidos operativo | Validar / Rechazar / Listo para Entrega, recetas adjuntas | HU-10 |
| PDF orden de trabajo | Generado con ReportLab | HU-11 |
| Dashboard gerencial | KPIs, 3 gráficos Chart.js, alertas de stock, exportación CSV | HU-12, HU-14 |
| Métricas VTO | Tasa de conversión VTO→pedido en el dashboard | HU-13 |
| Historial | Cliente ve sus pedidos; Gerencia ve todos con búsqueda | HU-15 |
| Integración n8n | Webhooks fire-and-forget para pedido validado y stock crítico | — |

## Stack

| Capa | Tecnología |
|------|------------|
| Backend / Negocio | Django 5 + Django REST Framework |
| Base de datos | PostgreSQL 16 |
| Frontend / Presentación | HTML / CSS / JS + Bootstrap 5 |
| Prueba Virtual (VTO) | OpenCV.js (WASM, clasificadores Haar) |
| Visualización | Chart.js 4 |
| Integración | n8n |
| Orquestación | Docker Compose |
