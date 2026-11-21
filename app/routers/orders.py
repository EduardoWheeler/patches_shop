from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import require_admin
from app.models import Order
from app.schemas import OrderCreate, OrderOut, OrderStatusUpdate
from app.services.order_service import OrderError, create_order, set_order_status

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=201)
def place_order(data: OrderCreate, db: Session = Depends(get_db)):
    try:
        return create_order(db, data)
    except OrderError as exc:
        db.rollback()
        raise HTTPException(exc.status_code, exc.message)


@router.get("", response_model=list[OrderOut], dependencies=[Depends(require_admin)])
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).order_by(Order.created_at.desc()).limit(200).all()


@router.get("/{order_id}", response_model=OrderOut, dependencies=[Depends(require_admin)])
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Pedido no encontrado")
    return order


@router.patch("/{order_id}/status", response_model=OrderOut, dependencies=[Depends(require_admin)])
def update_status(order_id: int, data: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Pedido no encontrado")
    try:
        return set_order_status(db, order, data.status)
    except OrderError as exc:
        db.rollback()
        raise HTTPException(exc.status_code, exc.message)
