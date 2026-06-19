from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Turno, Cliente
from app.schemas import TurnoCreate, TurnoResponse, TurnoUpdate
from services.notifications import enviar_correo_cliente_propietario, notificar_turno_confirmado, enviar_recordatorio_turnos
from services.auth import verify_client_token

router = APIRouter(prefix="/api/turnos", tags=["Turnos"])

# TODO: Implementar autenticación por número de WhatsApp del cliente

@router.post("/", response_model=TurnoResponse)
async def crear_turno(
    turno: TurnoCreate,
    cliente_numero: str,
    db: Session = Depends(get_db),
    current_cliente: Cliente = Depends(verify_client_token)
):
    """
    Crea un nuevo turno. El cliente es identificado por su número de WhatsApp
    """
    # Buscar cliente por número
    cliente = db.query(Cliente).filter(Cliente.numero_whatsapp == cliente_numero).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    nuevo_turno = Turno(
        cliente_id=cliente.id,
        cliente_numero=cliente_numero,
        fecha_turno=turno.fecha_turno,
        descripcion=turno.descripcion,
        estado="confirmado"
    )
    
    db.add(nuevo_turno)
    db.commit()
    db.refresh(nuevo_turno)

    # Notificar a cliente propietario por email
    await enviar_correo_cliente_propietario(cliente, nuevo_turno)

    # Notificar al usuario que solicitó el turno por Whatsapp
    await notificar_turno_confirmado(cliente_numero, turno.fecha_turno)

    return nuevo_turno

@router.get("/{turno_id}", response_model=TurnoResponse)
async def obtener_turno(turno_id: int, db: Session = Depends(get_db), current_cliente: Cliente = Depends(verify_client_token)):
    """Obtiene detalles de un turno"""
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return turno

@router.put("/{turno_id}", response_model=TurnoResponse)
async def actualizar_turno(
    turno_id: int,
    turno_update: TurnoUpdate,
    db: Session = Depends(get_db),
    current_cliente: Cliente = Depends(verify_client_token)
):
    """Actualiza el estado de un turno"""
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    
    turno.estado = turno_update.estado
    db.commit()
    db.refresh(turno)
    
    return turno

@router.get("/cliente/{numero_whatsapp}")
async def listar_turnos_cliente(numero_whatsapp: str, db: Session = Depends(get_db), current_cliente: Cliente = Depends(verify_client_token)):
    """Lista todos los turnos de un cliente"""
    cliente = db.query(Cliente).filter(Cliente.numero_whatsapp == numero_whatsapp).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    turnos = db.query(Turno).filter(Turno.cliente_id == cliente.id).all()
    return turnos

@router.post("/recordatorio")
async def ejecutar_recordatorio_mensajes(db: Session = Depends(get_db), current_cliente: Cliente = Depends(verify_client_token)):
    """Ejecuta el envio de recordatorios de turnos en 24h"""
    await enviar_recordatorio_turnos(db)
    return {"message": "Recordatorios enviados (o intentados)"}
