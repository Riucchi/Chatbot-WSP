import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from app.database import init_db
from app.routers import webhooks, turnos, admin, dashboard

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Inicializando base de datos...")
    init_db()
    logger.info("Base de datos lista")
    yield
    # Shutdown (si es necesario)

# Crear aplicación
app = FastAPI(
    title="WhatsApp Bot - Multi-Tenant",
    description="Bot dinámico para gestionar clientes con WhatsApp Business API",
    version="1.0.0",
    lifespan=lifespan
)

# Routers
app.include_router(webhooks.router)
app.include_router(turnos.router)
app.include_router(admin.router)
app.include_router(dashboard.router)

@app.get("/")
async def root():
    return {
        "mensaje": "WhatsApp Bot API - Multi-Tenant",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug
    )
    