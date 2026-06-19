from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import get_settings
from app.models import Base

settings = get_settings()

# Crear engine
engine = create_engine(settings.database_url, echo=True)

# SessionLocal para crear sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Crea todas las tablas"""
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """Dependency para obtener sesión en endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
