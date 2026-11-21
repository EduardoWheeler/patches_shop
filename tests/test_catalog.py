def test_public_list_hides_inactive(client, catalog):
    names = [p["name"] for p in client.get("/api/products").json()]
    assert "Parche redondo" in names
    assert "Descatalogado" not in names


def test_filter_by_category_and_search(client, catalog):
    by_category = client.get("/api/products", params={"category_id": catalog["other"]}).json()
    assert [p["name"] for p in by_category] == ["Parche PVC 3D"]
    by_text = client.get("/api/products", params={"q": "escudo"}).json()
    assert [p["name"] for p in by_text] == ["Parche escudo"]


def test_get_inactive_product_is_404(client, catalog):
    assert client.get("/api/products/" + str(catalog["hidden"])).status_code == 404


def product_body(catalog, **extra):
    body = {"category_id": catalog["category"], "name": "Nuevo parche", "price": "3.25", "stock": 20}
    body.update(extra)
    return body


def test_create_product_requires_admin(client, catalog):
    assert client.post("/api/products", json=product_body(catalog)).status_code == 401


def test_admin_product_crud(client, catalog, admin_headers):
    created = client.post("/api/products", json=product_body(catalog), headers=admin_headers)
    assert created.status_code == 201
    product_id = created.json()["id"]

    updated = client.put(
        "/api/products/" + str(product_id),
        json=product_body(catalog, name="Renombrado", stock=7),
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Renombrado"
    assert updated.json()["stock"] == 7

    assert client.delete("/api/products/" + str(product_id), headers=admin_headers).status_code == 204
    assert client.get("/api/products/" + str(product_id)).status_code == 404
    assert product_id not in [p["id"] for p in client.get("/api/products").json()]


def test_create_product_unknown_category(client, catalog, admin_headers):
    response = client.post("/api/products", json=product_body(catalog, category_id=9999), headers=admin_headers)
    assert response.status_code == 404


def test_product_validation(client, catalog, admin_headers):
    for bad in ({"price": "0"}, {"stock": -1}, {"name": ""}):
        response = client.post("/api/products", json=product_body(catalog, **bad), headers=admin_headers)
        assert response.status_code == 422


def test_image_url_must_be_local_upload(client, catalog, admin_headers):
    external = client.post(
        "/api/products", json=product_body(catalog, image_url="https://evil.example/x.png"), headers=admin_headers
    )
    assert external.status_code == 422
    local = client.post(
        "/api/products", json=product_body(catalog, image_url="/static/uploads/abc123.png"), headers=admin_headers
    )
    assert local.status_code == 201
    assert local.json()["image_url"] == "/static/uploads/abc123.png"


def test_category_duplicate_slug(client, catalog, admin_headers):
    response = client.post("/api/categories", json={"name": "Otra", "slug": "bordados"}, headers=admin_headers)
    assert response.status_code == 409
    created = client.post("/api/categories", json={"name": "Tejidos", "slug": "tejidos"}, headers=admin_headers)
    assert created.status_code == 201
    assert "tejidos" in [c["slug"] for c in client.get("/api/categories").json()]
