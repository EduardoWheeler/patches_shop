import os

# Debe fijarse antes de importar la aplicación.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "clave-solo-para-tests-0123456789-abcdefghijklmnop"

from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import models  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.security import hash_password  # noqa: E402


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Sin "with": no se ejecuta el lifespan (ni seed ni conexión a MySQL).
    yield TestClient(app)
    app.dependency_overrides.clear()


def _login_headers(client, session_factory, email, role):
    with session_factory() as db:
        db.add(models.User(email=email, password_hash=hash_password("clave-segura-1"), role=role))
        db.commit()
    response = client.post("/api/auth/login", json={"email": email, "password": "clave-segura-1"})
    return {"Authorization": "Bearer " + response.json()["access_token"]}


@pytest.fixture()
def admin_headers(client, session_factory):
    return _login_headers(client, session_factory, "admin@test.com", "admin")


@pytest.fixture()
def customer_headers(client, session_factory):
    return _login_headers(client, session_factory, "cliente@test.com", "customer")


@pytest.fixture()
def catalog(session_factory):
    with session_factory() as db:
        category = models.Category(name="Bordados", slug="bordados")
        other = models.Category(name="PVC", slug="pvc")
        db.add_all([category, other])
        db.flush()
        a = models.Product(category_id=category.id, name="Parche redondo", price=Decimal("4.50"), stock=10, size="7 cm")
        b = models.Product(category_id=category.id, name="Parche escudo", price=Decimal("5.20"), stock=2)
        c = models.Product(category_id=other.id, name="Parche PVC 3D", price=Decimal("6.80"), stock=5)
        hidden = models.Product(category_id=category.id, name="Descatalogado", price=Decimal("1.00"), stock=5, is_active=False)
        db.add_all([a, b, c, hidden])
        db.commit()
        return {"category": category.id, "other": other.id, "a": a.id, "b": b.id, "c": c.id, "hidden": hidden.id}
