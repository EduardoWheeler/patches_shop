from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Order, OrderItem, Product
from app.schemas import OrderCreate


class OrderError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def create_order(db: Session, data: OrderCreate) -> Order:
    ids = {item.product_id for item in data.items}
    products = {
        p.id: p
        for p in db.query(Product)
        .filter(Product.id.in_(ids), Product.is_active.is_(True))
        .with_for_update()
        .all()
    }
    order = Order(
        customer_name=data.customer_name,
        customer_email=data.customer_email,
        shipping_address=data.shipping_address,
        status="pending",
        total=Decimal("0"),
    )
    total = Decimal("0")
    for item in data.items:
        product = products.get(item.product_id)
        if product is None:
            raise OrderError(f"El producto {item.product_id} no existe o no está disponible", 404)
        if product.stock < item.quantity:
            raise OrderError(f"Stock insuficiente para '{product.name}' (quedan {product.stock})")
        product.stock -= item.quantity
        price = Decimal(product.price)
        total += price * item.quantity
        order.items.append(
            OrderItem(
                product_id=product.id,
                quantity=item.quantity,
                unit_price=price,
                custom_text=item.custom_text,
            )
        )
    order.total = total
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def set_order_status(db: Session, order: Order, new_status: str) -> Order:
    if order.status == new_status:
        return order
    if order.status == "cancelled":
        raise OrderError("Un pedido cancelado no puede reabrirse")
    if new_status == "cancelled":
        ids = [item.product_id for item in order.items]
        products = {
            p.id: p
            for p in db.query(Product).filter(Product.id.in_(ids)).with_for_update().all()
        }
        for item in order.items:
            products[item.product_id].stock += item.quantity
    order.status = new_status
    db.commit()
    db.refresh(order)
    return order
