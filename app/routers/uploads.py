import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.security import require_admin

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads"
MAX_BYTES = 2 * 1024 * 1024

router = APIRouter(prefix="/api/uploads", tags=["uploads"], dependencies=[Depends(require_admin)])


def detect_extension(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


@router.post("", status_code=201)
async def upload_image(file: UploadFile = File(...)):
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "La imagen supera los 2 MB")
    extension = detect_extension(data)
    if extension is None:
        raise HTTPException(400, "Formato no permitido (usa PNG, JPG o WEBP)")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = uuid.uuid4().hex + extension
    (UPLOAD_DIR / name).write_bytes(data)
    return {"url": "/static/uploads/" + name}
