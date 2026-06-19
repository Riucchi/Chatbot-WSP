from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Cliente, Turno
from services.auth import verify_client_token, require_role

router = APIRouter(prefix="/admin", tags=["Dashboard"])
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    estado: str | None = None,
    fecha: str | None = None,
    db: Session = Depends(get_db),
    current_cliente = Depends(verify_client_token)
):
    require_role(current_cliente, ["admin", "owner"])
    clientes = db.query(Cliente).all()

    turnos_query = db.query(Turno)
    if estado:
        turnos_query = turnos_query.filter(Turno.estado == estado)
    if fecha:
        try:
            fecha_obj = datetime.fromisoformat(fecha)
            siguiente = fecha_obj + timedelta(days=1)
            turnos_query = turnos_query.filter(Turno.fecha_turno >= fecha_obj, Turno.fecha_turno < siguiente)
        except ValueError:
            pass

    turnos = turnos_query.order_by(Turno.fecha_turno).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "clientes": clientes,
        "turnos": turnos,
        "filtro_estado": estado or "",
        "filtro_fecha": fecha or "",
    })
