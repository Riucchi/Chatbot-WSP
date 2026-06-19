import logging
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Turno, Cliente
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def enviar_correo_cliente_propietario(cliente: Cliente, turno: Turno):
    """Envía un email al cliente que paga el servicio cuando se pide un turno"""
    asunto = f"Nuevo turno solicitado: {turno.fecha_turno.strftime('%d/%m/%Y %H:%M')}"
    cuerpo = (
        f"Se ha solicitado un nuevo turno para el cliente {turno.cliente_numero}.\n"
        f"Fecha/horario: {turno.fecha_turno.strftime('%d/%m/%Y %H:%M')}\n"
        f"Estado: {turno.estado}\n"
        f"Descripción: {turno.descripcion or 'Sin descripción'}\n"
    )

    mensaje = EmailMessage()
    mensaje["From"] = settings.email_from
    mensaje["To"] = cliente.email
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(mensaje)
        logger.info(f"Email enviado a {cliente.email}")
        return True
    except Exception as e:
        logger.error(f"Error enviando email a {cliente.email}: {e}")
        return False

async def enviar_recordatorio_turnos(db: Session):
    """Envía recordatorios de turnos próximos (24 horas antes)"""
    from services.whatsapp import whatsapp_service  # Importar aquí para evitar circular import
    
    manana = datetime.utcnow() + timedelta(days=1)
    intervalo_fin = manana + timedelta(hours=1)

    turnos = db.query(Turno).filter(
        Turno.fecha_turno.between(manana, intervalo_fin),
        Turno.estado == "confirmado"
    ).all()

    for turno in turnos:
        mensaje = f"Recordatorio: Tienes un turno mañana a las {turno.fecha_turno.strftime('%H:%M')}"
        await whatsapp_service.enviar_mensaje(turno.cliente_numero, mensaje)
        logger.info(f"Recordatorio enviado a {turno.cliente_numero}")

async def notificar_turno_confirmado(numero_cliente: str, fecha: datetime):
    """Notifica confirmación de turno"""
    from services.whatsapp import whatsapp_service  # Importar aquí para evitar circular import
    
    fecha_str = fecha.strftime("%d/%m/%Y a las %H:%M")
    mensaje = f"✅ Tu turno ha sido confirmado para el {fecha_str}"
    await whatsapp_service.enviar_mensaje(numero_cliente, mensaje)
