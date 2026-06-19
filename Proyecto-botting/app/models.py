from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Cliente(Base):
    """Representa un cliente/empresa que usa el servicio"""
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True)
    numero_whatsapp = Column(String(20), unique=True, nullable=False)
    nombre_empresa = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    api_key = Column(String(100), unique=True, nullable=False)
    rol = Column(String(20), default="owner")  # owner/admin/support
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    turnos = relationship("Turno", back_populates="cliente")
    
    def __repr__(self):
        return f"<Cliente {self.nombre_empresa} ({self.numero_whatsapp})>"

class Contacto(Base):
    """Contactos que interactúan con el bot (usuarios finales)"""
    __tablename__ = "contactos"

    id = Column(Integer, primary_key=True)
    wa_id = Column(String(30), unique=True, nullable=False)
    nombre = Column(String(255), nullable=True)
    primer_mensaje = Column(DateTime, default=datetime.utcnow)
    ultimo_mensaje = Column(DateTime, default=datetime.utcnow)
    mensajes_enviados = Column(Integer, default=0)

    def __repr__(self):
        return f"<Contacto {self.wa_id} - {self.nombre}>"    

class Turno(Base):
    """Gestión de turnos/citas"""
    __tablename__ = "turnos"
    
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    cliente_numero = Column(String(20), nullable=False)  # Número del cliente que solicita turno
    fecha_turno = Column(DateTime, nullable=False)
    descripcion = Column(Text)
    estado = Column(String(50), default="pendiente")  # pendiente, confirmado, completado, cancelado
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    cliente = relationship("Cliente", back_populates="turnos")
    
    def __repr__(self):
        return f"<Turno {self.id} - {self.estado}>"


