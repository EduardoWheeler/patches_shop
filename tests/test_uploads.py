import pytest

from app.routers import uploads

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32
JPG = b"\xff\xd8\xff\xe0" + b"0" * 32
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"0" * 32


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "UPLOAD_DIR", tmp_path)
    return tmp_path


def send(client, headers, content, filename="foto.png"):
    return client.post("/api/uploads", files={"file": (filename, content, "image/png")}, headers=headers)


@pytest.mark.parametrize("content,extension", [(PNG, ".png"), (JPG, ".jpg"), (WEBP, ".webp")])
def test_valid_images_are_saved(client, admin_headers, upload_dir, content, extension):
    response = send(client, admin_headers, content)
    assert response.status_code == 201
    url = response.json()["url"]
    assert url.startswith("/static/uploads/") and url.endswith(extension)
    assert (upload_dir / url.rsplit("/", 1)[1]).read_bytes() == content


def test_filename_is_never_trusted(client, admin_headers, upload_dir):
    response = send(client, admin_headers, PNG, filename="../../evil.php")
    assert response.status_code == 201
    saved = [p.name for p in upload_dir.iterdir()]
    assert len(saved) == 1 and saved[0].endswith(".png") and "evil" not in saved[0]


def test_rejects_non_image_with_image_extension(client, admin_headers, upload_dir):
    response = send(client, admin_headers, b"<?php echo 1; ?>", filename="foto.png")
    assert response.status_code == 400
    assert list(upload_dir.iterdir()) == []


def test_rejects_oversized_file(client, admin_headers):
    response = send(client, admin_headers, PNG + b"0" * (2 * 1024 * 1024))
    assert response.status_code == 413


def test_upload_requires_admin(client, customer_headers):
    assert send(client, {}, PNG).status_code == 401
    assert send(client, customer_headers, PNG).status_code == 403
