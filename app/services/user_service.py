from sqlalchemy.orm import Session

from app.config import ADMIN_EMAIL, ADMIN_PASSWORD
from app.models import User
from app.security import hash_password


def ensure_admin(db: Session) -> None:
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        return
    email = ADMIN_EMAIL.lower()
    if db.query(User).filter(User.email == email).first():
        return
    db.add(User(email=email, password_hash=hash_password(ADMIN_PASSWORD), role="admin"))
    db.commit()
