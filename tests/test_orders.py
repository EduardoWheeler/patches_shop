from decimal import Decimal

from app import models


def payload(items, **extra):
    data = {
        "customer_name": "Ana Pérez",
        "customer_email": "ana@example.com",
        "shipping_address": "Calle Falsa 123",
        "items": items,
    }
    data.update(extra)
    return data


def stock(client, product_id):
    return client.get("/api/products/" + str(product_id)).json()["stock"]


def test_create_order_discounts_stock_and_computes_total(client, catalog):
    items = [
        {"product_id": catalog["a"], "quantity": 3, "custom_text": "Club Atlético"},
        {"product_id": catalog["b"], "quantity": 1},
    ]
    response = client.post("/api/orders", json=payload(items))
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert Decimal(body["total"]) == Decimal("18.70")  # 3 x 4.50 + 1 x 5.20
    assert body["items"][0]["custom_text"] == "Club Atlético"
    assert Decimal(body["items"][0]["unit_price"]) == Decimal("4.50")
    assert stock(client, catalog["a"]) == 7
    assert stock(client, catalog["b"]) == 1


def test_insufficient_stock_rolls_back_everything(client, catalog, session_factory):
    items = [
        {"product_id": catalog["a"], "quantity": 1},
        {"product_id": catalog["b"], "quantity": 3},  # solo hay 2
    ]
    response = client.post("/api/orders", json=payload(items))
    assert response.status_code == 400
    assert "Stock insuficiente" in response.json()["detail"]
    assert stock(client, catalog["a"]) == 10
    assert stock(client, catalog["b"]) == 2
    with session_factory() as db:
        assert db.query(models.Order).count() == 0


def test_order_unknown_or_inactive_product(client, catalog):
    for product_id in (9999, catalog["hidden"]):
        response = client.post("/api/orders", json=payload([{"product_id": product_id, "quantity": 1}]))
        assert response.status_code == 404


def test_order_validation(client, catalog):
    item = [{"product_id": catalog["a"], "quantity": 1}]
    assert client.post("/api/orders", json=payload([])).status_code == 422
    assert client.post("/api/orders", json=payload(item, customer_email="no-es-email")).status_code == 422
    assert client.post("/api/orders", json=payload([{"product_id": catalog["a"], "quantity": 0}])).status_code == 422


def make_order(client, catalog, quantity=4):
    response = client.post("/api/orders", json=payload([{"product_id": catalog["a"], "quantity": quantity}]))
    return response.json()["id"]


def test_admin_can_list_and_read_orders(client, catalog, admin_headers):
    order_id = make_order(client, catalog)
    listing = client.get("/api/orders", headers=admin_headers)
    assert listing.status_code == 200
    assert [o["id"] for o in listing.json()] == [order_id]
    assert client.get("/api/orders/" + str(order_id), headers=admin_headers).status_code == 200
    assert client.get("/api/orders/9999", headers=admin_headers).status_code == 404


def test_status_flow(client, catalog, admin_headers):
    order_id = make_order(client, catalog)
    for status in ("paid", "shipped"):
        response = client.patch("/api/orders/" + str(order_id) + "/status", json={"status": status}, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["status"] == status
    invalid = client.patch("/api/orders/" + str(order_id) + "/status", json={"status": "volando"}, headers=admin_headers)
    assert invalid.status_code == 422


def test_cancel_restores_stock_only_once(client, catalog, admin_headers):
    order_id = make_order(client, catalog, quantity=4)
    assert stock(client, catalog["a"]) == 6
    url = "/api/orders/" + str(order_id) + "/status"

    assert client.patch(url, json={"status": "cancelled"}, headers=admin_headers).status_code == 200
    assert stock(client, catalog["a"]) == 10

    # Repetir la cancelación no vuelve a sumar stock.
    assert client.patch(url, json={"status": "cancelled"}, headers=admin_headers).status_code == 200
    assert stock(client, catalog["a"]) == 10


def test_cancelled_order_cannot_be_reopened(client, catalog, admin_headers):
    order_id = make_order(client, catalog)
    url = "/api/orders/" + str(order_id) + "/status"
    client.patch(url, json={"status": "cancelled"}, headers=admin_headers)
    response = client.patch(url, json={"status": "paid"}, headers=admin_headers)
    assert response.status_code == 400
    assert stock(client, catalog["a"]) == 10


def test_update_status_unknown_order(client, admin_headers):
    response = client.patch("/api/orders/9999/status", json={"status": "paid"}, headers=admin_headers)
    assert response.status_code == 404
