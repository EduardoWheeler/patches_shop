from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import SECRET_KEY
from app.security import hash_password, verify_password


def test_password_hash_roundtrip():
    stored = hash_password("mi-clave")
    assert stored != "mi-clave"
    assert verify_password("mi-clave", stored)
    assert not verify_password("otra", stored)
    assert hash_password("mi-clave") != stored  # sal distinta en cada hash
    assert not verify_password("mi-clave", "formato-invalido")


def test_login_and_me(client, admin_headers):
    response = client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "admin@test.com"
    assert response.json()["role"] == "admin"


def test_login_wrong_password(client, admin_headers):
    response = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "mala"})
    assert response.status_code == 401


def test_login_unknown_user(client):
    response = client.post("/api/auth/login", json={"email": "nadie@test.com", "password": "x"})
    assert response.status_code == 401


PROTECTED = [
    ("get", "/api/orders", None),
    ("get", "/api/orders/1", None),
    ("patch", "/api/orders/1/status", {"status": "paid"}),
    ("post", "/api/categories", {"name": "Nueva", "slug": "nueva"}),
    ("delete", "/api/products/1", None),
]


@pytest.mark.parametrize("method,path,body", PROTECTED)
def test_protected_routes_require_token(client, method, path, body):
    response = getattr(client, method)(path, **({"json": body} if body else {}))
    assert response.status_code == 401


@pytest.mark.parametrize("method,path,body", PROTECTED)
def test_protected_routes_reject_customers(client, customer_headers, method, path, body):
    kwargs = {"headers": customer_headers}
    if body:
        kwargs["json"] = body
    assert getattr(client, method)(path, **kwargs).status_code == 403


def test_invalid_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer basura"})
    assert response.status_code == 401


def test_expired_token(client, admin_headers):
    expired = jwt.encode(
        {"sub": "1", "role": "admin", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        SECRET_KEY,
        algorithm="HS256",
    )
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer " + expired}).status_code == 401


def test_token_signed_with_other_key(client, admin_headers):
    forged = jwt.encode(
        {"sub": "1", "role": "admin", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "otra-clave-distinta-0123456789-abcdefghijklmnop",
        algorithm="HS256",
    )
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer " + forged}).status_code == 401
