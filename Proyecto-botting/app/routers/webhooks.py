from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from config import get_settings
import json
import logging

from app.database import get_db
from app.models import Cliente
from services.whatsapp import procesar_mensaje

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook")
settings = get_settings()

@router.get("/whatsapp")
async def verificar_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    """
    Verificación inicial del webhook con Meta
    """
    if hub_mode == "subscribe":
        if hub_verify_token == settings.webhook_verify_token:
            logger.info("Webhook verificado correctamente")
            return int(hub_challenge)
        else:
            logger.error("Token de verificación inválido")
            raise HTTPException(status_code=403, detail="Token inválido")
    
    raise HTTPException(status_code=400, detail="Solicitud inválida")

@router.post("/whatsapp")
async def recibir_mensaje(request: Request, db: Session = Depends(get_db)):
    """
    Recibe mensajes de WhatsApp desde Meta
    """
    try:
        data = await request.json()
        logger.info(f"Mensaje recibido: {json.dumps(data)}")
        
        # Procesar el mensaje
        await procesar_mensaje(data, db)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
        return {"status": "error", "message": str(e)}
