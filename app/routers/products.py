from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import require_admin
from app.models import Category, Product
from app.schemas import ProductCreate, ProductOut

router = APIRouter(prefix="/api/products", tags=["products"])

@router.get("", response_model=list[ProductOut])
def list_products(
    category_id: int | None = None,
    q: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_active.is_(True))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if q:
        query = query.filter(Product.name.contains(q, autoescape=True))  # % y _ del usuario se tratan como texto
    return query.order_by(Product.created_at.desc()).all()

@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or not product.is_active:
        raise HTTPException(404, "Producto no encontrado")
    return product

@router.post("", response_model=ProductOut, status_code=201, dependencies=[Depends(require_admin)])
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    if not db.get(Category, data.category_id):
        raise HTTPException(404, "La categoría no existe")
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.put("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_admin)])
def update_product(product_id: int, data: ProductCreate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Producto no encontrado")
    for key, value in data.model_dump().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Producto no encontrado")
    product.is_active = False
    db.commit()
