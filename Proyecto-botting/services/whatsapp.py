import requests
import json
import logging
from datetime import datetime
from config import get_settings
from sqlalchemy.orm import Session
from app.models import Contacto, Cliente, Turno
from services.notifications import enviar_correo_cliente_propietario, notificar_turno_confirmado

logger = logging.getLogger(__name__)
settings = get_settings()

ENDPOINT_META = "https://graph.instagram.com/v18.0"

class WhatsAppService:
    def __init__(self):
        self.access_token = settings.meta_access_token
        self.phone_number_id = settings.meta_phone_number_id
        self.business_account_id = settings.meta_business_account_id
    
    async def enviar_mensaje(self, numero_destino: str, mensaje: str) -> bool:
        """
        Envía un mensaje de texto a través de Meta/WhatsApp
        """
        url = f"{ENDPOINT_META}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": numero_destino,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": mensaje
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            logger.info(f"Respuesta Meta: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"Mensaje enviado a {numero_destino}")
                return True
            else:
                logger.error(f"Error enviando mensaje: {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Excepción enviando mensaje: {str(e)}")
            return False

async def _get_or_create_contacto(db: Session, wa_id: str, nombre: str | None):
    contacto = db.query(Contacto).filter(Contacto.wa_id == wa_id).first()
    if contacto:
        contacto.ultimo_mensaje = datetime.utcnow()
        contacto.mensajes_enviados += 1
        if nombre and not contacto.nombre:
            contacto.nombre = nombre
        db.commit()
        db.refresh(contacto)
        return contacto

    contacto = Contacto(
        wa_id=wa_id,
        nombre=nombre,
        primer_mensaje=datetime.utcnow(),
        ultimo_mensaje=datetime.utcnow(),
        mensajes_enviados=1
    )
    db.add(contacto)
    db.commit()
    db.refresh(contacto)
    return contacto

async def procesar_mensaje(data: dict, db: Session):
    """
    Procesa mensajes entrantes del webhook de Meta

    - Detecta primer contacto y genera saludo predeterminado
    - Si ya existía, procesa intención para turno
    - Responde texto clásico cuando no se reconoce intención
    """
    try:
        logger.info(f"Procesando mensaje: {json.dumps(data)}")

        entry = data.get("entry", [])
        if not entry:
            raise ValueError("Payload sin entry")

        change = entry[0].get("changes", [])[0]
        value = change.get("value", {})
        messages = value.get("messages", [])
        if not messages:
            logger.info("Sin mensajes a procesar")
            return

        message = messages[0]
        from_number = message.get("from")
        text_body = ""
        if message.get("type") == "text":
            text_body = message.get("text", {}).get("body", "").strip()

        contact_info = value.get("contacts", [])[0] if value.get("contacts") else {}
        nombre = contact_info.get("profile", {}).get("name")

        contacto = await _get_or_create_contacto(db, from_number, nombre)

        # Encuentra el cliente (dueño del número de negocio que recibe la consulta)
        metadata = value.get("metadata", {})
        numero_negocio = metadata.get("display_phone_number")
        cliente = db.query(Cliente).filter(Cliente.numero_whatsapp == numero_negocio).first()

        # Mensaje de bienvenida en primer contacto
        if contacto.mensajes_enviados == 1:
            saludo = (
                f"Hola {nombre or 'cliente'}! Gracias por escribir. "
                "Soy el asistente automático. Puedes escribir:\n"
                "1) 'Turno' para agendar cita\n"
                "2) 'Ayuda' para obtener ayuda\n"
            )
            await whatsapp_service.enviar_mensaje(from_number, saludo)
            return

        # Intención simple por keywords
        intent = text_body.lower()

        if "turno" in intent or "cita" in intent or intent.startswith("agendar"):
            respuesta_turno = (
                "Entendido, estás solicitando un turno. "
                "Por favor envía la fecha y hora en el formato: 'turno YYYY-MM-DD HH:MM'."
            )

            if intent.startswith("turno ") or intent.startswith("cita "):
                try:
                    partes = intent.split(" ", 2)
                    fecha_texto = partes[1] + " " + partes[2]
                    fecha_turno = datetime.fromisoformat(fecha_texto)

                    if not cliente:
                        await whatsapp_service.enviar_mensaje(from_number, "No pude identificar tu empresa; contacta al admin del servicio.")
                        return

                    nuevo_turno = Turno(
                        cliente_id=cliente.id,
                        cliente_numero=from_number,
                        fecha_turno=fecha_turno,
                        descripcion=f"Turno automático desde WhatsApp: {text_body}",
                        estado="confirmado"
                    )
                    db.add(nuevo_turno)
                    db.commit()
                    db.refresh(nuevo_turno)

                    # Enviar notificación al cliente que paga el servicio (email)
                    await enviar_correo_cliente_propietario(cliente, nuevo_turno)

                    # Enviar confirmación whatsapp al solicitante
                    await notificar_turno_confirmado(from_number, fecha_turno)

                    respuesta_turno = (
                        f"Turno registrado y confirmado para {fecha_turno.strftime('%d/%m/%Y %H:%M')}. "
                        "Te enviaré un recordatorio 24 horas antes."
                    )
                except Exception:
                    respuesta_turno = (
                        "No pude entender la fecha/hora. Usa: 'turno YYYY-MM-DD HH:MM'. "
                        "Ej: turno 2026-04-07 10:30"
                    )

            await whatsapp_service.enviar_mensaje(from_number, respuesta_turno)
            return

        if "ayuda" in intent or "help" in intent:
            await whatsapp_service.enviar_mensaje(from_number, (
                "Escribe: Turno | Ayuda.\n"
                "Para turno envía 'turno YYYY-MM-DD HH:MM'."
            ))
            return

        # Mensaje por defecto
        await whatsapp_service.enviar_mensaje(from_number, (
            "Gracias por tu mensaje. Responde:\n"
            "- Turno\n"
            "- Ayuda"
        ))

    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}")

# Instancia global
whatsapp_service = WhatsAppService()
