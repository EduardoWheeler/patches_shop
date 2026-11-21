from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import require_admin
from app.models import Category
from app.schemas import CategoryCreate, CategoryOut

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


@router.post("", response_model=CategoryOut, status_code=201, dependencies=[Depends(require_admin)])
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    if db.query(Category).filter(Category.slug == data.slug).first():
        raise HTTPException(409, "Ya existe una categoría con ese slug")
    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
