from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config import get_settings
from app.models import Cliente
from app.database import get_db

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/token")

class TokenData:
    sub: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expires_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_client_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        cliente_id: str = payload.get("sub")
        if cliente_id is None:
            raise credentials_exception
        token_data = TokenData()
        token_data.sub = cliente_id
    except JWTError:
        raise credentials_exception

    cliente = db.query(Cliente).filter(Cliente.id == int(token_data.sub)).first()
    if cliente is None or not cliente.activo:
        raise credentials_exception
    return cliente


def require_role(cliente: Cliente, roles: list[str]):
    if cliente.rol not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos suficientes")
    return cliente



def authenticate_client(api_key: str, db: Session):
    cliente = db.query(Cliente).filter(Cliente.api_key == api_key).first()
    if not cliente or not cliente.activo:
        return None
    return cliente
