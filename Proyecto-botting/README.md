# WhatsApp Bot - Multi-Tenant Service

API REST para gestionar múltiples clientes/empresas a través de WhatsApp Business API de Meta.

## Estructura del Proyecto

```
Proyecto-botting/
├── main.py                      # Punto de entrada FastAPI
├── config.py                    # Configuración (carga desde .env)
├── requirements.txt             # Dependencias Python
├── .env                         # Variables de entorno (no commits)
│
├── app/                         # Lógica de la aplicación
│   ├── models.py               # Modelos SQLAlchemy (BD)
│   ├── schemas.py              # Esquemas Pydantic (validación)
│   ├── database.py             # Conexión PostgreSQL
│   └── routers/
│       ├── webhooks.py         # Endpoint POST/GET para Meta
│       ├── turnos.py           # Gestión de turnos/citas
│       └── admin.py            # Panel de administración
│
└── services/                    # Lógica de negocio
    ├── whatsapp.py             # Integración con Meta API
    └── notifications.py        # Notificaciones automáticas
```

## Configuración Inicial

### 1. Variables de Entorno

Edita `.env` con tus datos:

```env
# Base de Datos (SQLite para desarrollo, PostgreSQL para producción)
DATABASE_URL=sqlite:///./whatsapp_bot.db
# O para PostgreSQL: DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/whatsapp_bot

META_ACCESS_TOKEN=tu_access_token_obtén_de_meta_developers
META_PHONE_NUMBER_ID=tu_phone_id_de_meta
META_BUSINESS_ACCOUNT_ID=tu_business_account_id
WEBHOOK_VERIFY_TOKEN=tu_token_secreto_para_webhooks
SERVER_PORT=8000
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Base de Datos

Para SQLite (desarrollo): Se crea automáticamente al ejecutar el proyecto.

Para PostgreSQL (producción):
```bash
# En Windows (si PostgreSQL está instalado)
# Crear base de datos
createdb whatsapp_bot
```

### 4. Ejecutar la Aplicación

```bash
python main.py
```

La API estará disponible en: `http://localhost:8000`

## Endpoints Principales

### Webhook (Meta)
- **GET** `/webhook/whatsapp` - Verificación inicial
- **POST** `/webhook/whatsapp` - Recibe mensajes de Meta

### Turnos
- **POST** `/api/turnos/` - Crear turno
- **GET** `/api/turnos/{turno_id}` - Obtener turno
- **PUT** `/api/turnos/{turno_id}` - Actualizar estado
- **GET** `/api/turnos/cliente/{numero_whatsapp}` - Listar turnos

### Auth / Admin
- **POST** `/api/admin/token` - Obtener JWT (OAuth2 password flow, usa `password`=api_key)
- **POST** `/api/admin/clientes` - Registrar nuevo cliente (requiere JWT, rol admin)
- **GET** `/api/admin/clientes` - Listar todos (requiere JWT, rol admin/owner)
- **GET** `/api/admin/clientes/{cliente_id}` - Detalles (requiere JWT, rol admin/owner)
- **DELETE** `/api/admin/clientes/{cliente_id}` - Desactivar (requiere JWT, rol admin)
- **PUT** `/api/admin/clientes/{cliente_id}/activar` - Activar cliente (requiere admin)
- **PUT** `/api/admin/clientes/{cliente_id}/desactivar` - Desactivar cliente (requiere admin)
- **PUT** `/api/admin/clientes/{cliente_id}/rol?rol=admin|owner|support` - Cambiar rol (requiere admin)
- **GET** `/admin/dashboard` - Interfaz web (requiere JWT Bearer, rol admin/owner)

## Autenticación JWT

1. Registra un cliente por el endpoint admin (o en DB). Obtendrás `api_key`.
2. Solicita token con:

```bash
curl -X POST "http://localhost:8000/api/admin/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=any&password=sk_..."
```

3. Usa el token en cabezera `Authorization: Bearer <token>` en rutas protegidas.

## Flujo Multi-Tenant

1. **Registrar Cliente**: Admin crea cliente con número de WhatsApp
2. **Cliente interactúa**: Envía mensaje a tu número de WhatsApp Business
3. **Webhook recibe**: Meta envía POST a `/webhook/whatsapp`
4. **Identificar**: Sistema identifica cliente por número
5. **Procesar**: Según contexto crea turno
6. **Responder**: Envía confirmación automática por WhatsApp

## TODO (Por Implementar)

- [ ] Autenticación de clientes (JWT con API Key)
- [ ] Lógica completa de procesamiento de mensajes en `procesar_mensaje()`
- [x] Notificaciones programadas (Celery, cron o APScheduler)
- [x] Dashboard web para admin
- [ ] Tests unitarios

## Documentación

Abierta en: `http://localhost:8000/docs` (Swagger UI)

## Notas

- Todos los números deben incluir código de país (ej: +5491234567890)
- Los clientes se identifican por el número de WhatsApp (multi-tenant)
- Actualmente no hay autenticación, implementar antes de producción
