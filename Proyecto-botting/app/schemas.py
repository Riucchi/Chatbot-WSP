from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ===== CLIENTE =====
class ClienteCreate(BaseModel):
    numero_whatsapp: str
    nombre_empresa: str
    email: str
    rol: Optional[str] = "owner"

class ClienteResponse(BaseModel):
    id: int
    numero_whatsapp: str
    nombre_empresa: str
    email: str
    rol: str
    api_key: str
    activo: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

# ===== TURNO =====
class TurnoCreate(BaseModel):
    fecha_turno: datetime
    descripcion: Optional[str] = None

class TurnoResponse(BaseModel):
    id: int
    cliente_id: int
    cliente_numero: str
    fecha_turno: datetime
    descripcion: Optional[str]
    estado: str
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class TurnoUpdate(BaseModel):
    estado: str  # pendiente, confirmado, completado, cancelado


# ===== WEBHOOK DE META =====
class MessageData(BaseModel):
    from_number: str
    message_text: str
    message_type: str  # text, image, etc
    
class WebhookMessage(BaseModel):
    object: str
    entry: list
