# Capa de integración — n8n

Este documento describe cómo funciona la integración entre Django y n8n en el
demo, y cómo importar los flujos de trabajo para que se puedan demostrar.

## Arquitectura

```
Django (web:8000)
    │
    │  POST /webhook/pedido-validado  {pedido_id, usuario_email, total, estado}
    │  POST /webhook/stock-critico    {producto_id, nombre, stock_actual, …}
    ▼
n8n (n8n:5678)  ←→  interfaz en http://localhost:5678
    │
    └─ flujos de demostración: log en consola + respuesta 200
```

Django llama a n8n de forma **fire-and-forget con timeout de 3 segundos**.
Si n8n no responde o no está levantado, se registra un warning y el flujo
principal de Django continúa sin errores.

## Cuándo se disparan los webhooks

| Evento | Webhook | Vista de Django |
|---|---|---|
| Ventas/Gerencia valida un pedido | `pedido-validado` | `ValidarPedidoView` |
| Stock de un producto cae al mínimo tras un checkout | `stock-critico` | `checkout` |

## Levantar el stack completo

```bash
docker compose up --build
```

- Django: http://localhost:8000  
- n8n: http://localhost:5678 (sin autenticación en modo demo)

## Importar los flujos en n8n

> **IMPORTANTE — Sin este paso los webhooks devuelven 404.**  
> Los flujos deben estar importados **y activos** para que Django pueda
> llamarlos. Los JSON incluyen `"active": true`, por lo que n8n los activa al
> importar; si el toggle aparece en Off, activarlo manualmente.

Los flujos de demostración están versionados en `/integracion/n8n/`.

### Pasos

1. Abrir http://localhost:5678 en el navegador.
2. En el menú lateral, ir a **Workflows → Add workflow → Import from file**.
3. Importar `integracion/n8n/pedido_validado.json`.
4. Importar `integracion/n8n/stock_critico.json`.
5. Verificar que ambos muestren el toggle en **Active** (verde).

### Verificar que los webhooks están activos

Con el flujo activo, la URL de producción es:

```
http://localhost:5678/webhook/pedido-validado
http://localhost:5678/webhook/stock-critico
```

Para probar manualmente:

```bash
curl -X POST http://localhost:5678/webhook/pedido-validado \
  -H "Content-Type: application/json" \
  -d '{"pedido_id": 1, "usuario_email": "test@demo.com", "total": "25000", "estado": "En Proceso de Armado", "usuario_nombre": "Test User"}'
```

## Flujos disponibles

### `pedido_validado.json`

**Trigger:** `POST /webhook/pedido-validado`  
**Payload:**
```json
{
  "pedido_id": 42,
  "usuario_email": "cliente@demo.com",
  "usuario_nombre": "Ana García",
  "total": "38500.00",
  "estado": "En Proceso de Armado"
}
```
**Qué hace:** simula el envío de un email al cliente confirmando que su pedido
fue aprobado. El log aparece en la consola del contenedor n8n y en la vista de
ejecuciones de n8n (Executions).

---

### `stock_critico.json`

**Trigger:** `POST /webhook/stock-critico`  
**Payload:**
```json
{
  "producto_id": 7,
  "nombre": "Armazón Redondo Vintage",
  "marca": "Ray-Ban",
  "stock_actual": 2,
  "stock_minimo": 3,
  "deficit": 1
}
```
**Qué hace:** clasifica la alerta como `STOCK_MINIMO` o `SIN_STOCK`, imprime
la alerta en consola y responde con JSON estructurado. En un flujo real se
conectaría un nodo de email o Slack.

## Configuración Django

El setting `N8N_WEBHOOK_BASE` controla la URL base. Se inyecta desde
`docker-compose.yml`:

```yaml
environment:
  N8N_WEBHOOK_BASE: "http://n8n:5678/webhook"
```

Si la variable está vacía (por ejemplo en tests o desarrollo local sin Docker),
los webhooks se omiten silenciosamente.

## Extensión para producción

Para convertir estos flujos de demo en producción bastaría:

1. Reemplazar el nodo "Code (console.log)" por un nodo **Gmail / SMTP / Slack**.
2. Activar autenticación en n8n (`N8N_BASIC_AUTH_ACTIVE=true`).
3. Configurar `N8N_WEBHOOK_BASE` con la URL pública de n8n.
4. Agregar la cabecera `X-Webhook-Secret` en Django y verificarla en n8n.
