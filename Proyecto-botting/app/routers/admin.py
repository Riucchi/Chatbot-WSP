from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import uuid

from config import get_settings
from app.database import get_db
from app.models import Cliente
from app.schemas import ClienteCreate, ClienteResponse
from services.auth import authenticate_client, create_access_token, verify_client_token, require_role

settings = get_settings()
router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Obtiene token JWT usando api_key como password"""
    cliente = authenticate_client(form_data.password, db)
    if not cliente:
        raise HTTPException(status_code=401, detail="API key inválida")

    access_token_expires = timedelta(minutes=settings.jwt_access_token_expires_minutes)
    access_token = create_access_token(
        data={"sub": str(cliente.id)},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/clientes", response_model=ClienteResponse)
async def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db), current_cliente: Cliente = Depends(verify_client_token)):
    """Crea un nuevo cliente"""
    require_role(current_cliente, ["admin"])    
    # Verificar que no exista
    existente = db.query(Cliente).filter(Cliente.numero_whatsapp == cliente.numero_whatsapp).first()
    if existente:
        raise HTTPException(status_code=400, detail="Cliente ya existe")
    
    # Generar API Key única
    api_key = f"sk_{uuid.uuid4().hex[:32]}"
    
    nuevo_cliente = Cliente(
        numero_whatsapp=cliente.numero_whatsapp,
        nombre_empresa=cliente.nombre_empresa,
        email=cliente.email,
        rol=cliente.rol,
        api_key=api_key,
        activo=True
    )
    
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    
    return nuevo_cliente

@router.get("/clientes", response_model=list[ClienteResponse])
async def listar_clientes(db: Session = Depends(get_db), current_cliente: Cliente = Depends(verify_client_token)):
    """Lista todos los clientes"""
    require_role(current_cliente, ["admin", "owner"])
    clientes = db.query(Cliente).all()
    return clientes

@router.get("/clientes/{cliente_id}", response_model=ClienteResponse)
async def obtener_cliente(cliente_id: int, db: Session = Depends(get_db), current_cliente: Cliente = Depends(verify_client_token)):
    """Obtiene detalles de un cliente"""
    require_role(current_cliente, ["admin", "owner"])
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.delete("/clientes/{cliente_id}")
async def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db), current_cliente: Cliente = Depends(verify_client_token)):
    """Desactiva un cliente"""
    require_role(current_cliente, ["admin"])
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    cliente.activo = False
    db.commit()
    
    return {"message": "Cliente desactivado"}

@router.put("/clientes/{cliente_id}/activar")
async def activar_cliente(cliente_id: int, db: Session = Depends(get_db), current_cliente: Cliente = Depends(verify_client_token)):
    require_role(current_cliente, ["admin"])
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    cliente.activo = True
    db.commit()
    return {"message": "Cliente activado"}

@router.put("/clientes/{cliente_id}/desactivar")
async def desactivar_cliente(cliente_id: int, db: Session = Depends(get_db), current_cliente: Cliente = Depends(verify_client_token)):
    require_role(current_cliente, ["admin"])
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    cliente.activo = False
    db.commit()
    return {"message": "Cliente desactivado"}

@router.put("/clientes/{cliente_id}/rol")
async def cambiar_rol_cliente(cliente_id: int, rol: str, db: Session = Depends(get_db), current_cliente: Cliente = Depends(verify_client_token)):
    require_role(current_cliente, ["admin"])
    if rol not in ["admin", "owner", "support"]:
        raise HTTPException(status_code=400, detail="Rol inválido")
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    cliente.rol = rol
    db.commit()
    return {"message": f"Rol cambiado a {rol}"}
