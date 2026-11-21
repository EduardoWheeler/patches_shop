from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import models
from app.database import SessionLocal
from app.services.user_service import ensure_admin
from app.routers import auth, categories, orders, products, uploads

STATIC_DIR = Path(__file__).parent / "static"


def seed_data():
    with SessionLocal() as db:
        if db.query(models.Category).count():
            return
        cats = [
            models.Category(name="Bordados", slug="bordados"),
            models.Category(name="PVC", slug="pvc"),
            models.Category(name="Tejidos", slug="tejidos"),
        ]
        db.add_all(cats)
        db.flush()
        db.add_all(
            [
                models.Product(category_id=cats[0].id, name="Parche bordado redondo", description="Bordado a todo color con borde merrow y respaldo termoadhesivo.", price=Decimal("4.50"), stock=200, size="7 cm"),
                models.Product(category_id=cats[0].id, name="Parche bordado escudo", description="Ideal para equipos y clubes. Hasta 8 colores.", price=Decimal("5.20"), stock=150, size="8 cm"),
                models.Product(category_id=cats[1].id, name="Parche PVC 3D", description="Goma flexible, resistente al agua, con velcro.", price=Decimal("6.80"), stock=120, size="6 cm"),
                models.Product(category_id=cats[2].id, name="Etiqueta tejida", description="Tejido fino de alta densidad para prendas.", price=Decimal("2.90"), stock=300, size="5 cm"),
            ]
        )
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_data()
    with SessionLocal() as db:
        ensure_admin(db)
    yield


app = FastAPI(title="Patches Shop API", version="1.0.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(uploads.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin", include_in_schema=False)
def admin_panel():
    return FileResponse(STATIC_DIR / "admin.html")
