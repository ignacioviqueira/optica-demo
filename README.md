# Sistema de Gestión Óptica — Demo

Prototipo del **Sistema Web de Gestión Comercial y Prueba Virtual para Ópticas**.  
Trabajo Final de Graduación · Universidad Siglo 21 · Ignacio Federico Viqueira.

## Levantar el proyecto

```bash
# 1. Clonar y entrar al directorio
git clone <repo-url> && cd optica-demo

# 2. Copiar variables de entorno
cp .env.example .env

# 3. Levantar stack completo (Django + PostgreSQL + n8n)
docker compose up --build

# 4. Aplicar migraciones (primera vez)
docker compose run web python manage.py migrate

# 5. Cargar datos de demo
docker compose run web python manage.py seed_demo

# 6. Correr tests
docker compose run web python manage.py test
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
| Gerencia | gerencia@optica.demo | `Gerencia@123` |
| Ventas | ventas@optica.demo | `Ventas@123` |
| Cliente | cliente@optica.demo | `Cliente@123` |

> Para acceder al admin de Django usá la cuenta de **Gerencia** (`is_staff=True`).

## Datos sembrados

El comando `seed_demo` carga:

- **3 usuarios** (uno por rol)
- **3 categorías**: Armazones, Cristales, Lentes de Contacto
- **15 productos** (5 por categoría), con 5 en stock crítico:
  - Prada PR 01OS (2 uds. / mín. 3)
  - Tom Ford FT5634-B (1 ud. / mín. 3)
  - Hoya ID MyStyle V+ (4 uds. / mín. 5)
  - Bausch+Lomb Ultra (3 uds. / mín. 10)
  - CooperVision Proclear (2 uds. / mín. 10)
- **3 recetas** para la usuaria cliente (fechas 2023–2025)
- **5 pedidos** en distintos estados:
  - 1 × Pendiente de Validación
  - 1 × En Proceso de Armado
  - 2 × Listo para Entrega
  - 1 × Rechazado (con motivo)

El seed es **idempotente**: ejecutarlo más de una vez no duplica registros.

## Stack

- **Backend:** Django 5 + PostgreSQL 16
- **Frontend:** HTML / CSS / JS + Bootstrap 5
- **VTO:** OpenCV.js (próxima fase)
- **Integración:** n8n
- **Orquestación:** Docker Compose
