import os
import secrets

# python-dotenv es opcional: si está instalado se lee .env; si no, se usa el entorno.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "Falta DATABASE_URL. Copia .env.example a .env o exporta la variable, p. ej.: "
        "mysql+pymysql://usuario:clave@localhost:3306/patches_db"
    )

# Si no defines SECRET_KEY se genera una aleatoria: los tokens dejan de ser válidos al reiniciar.
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(48)
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))

# Si ambos están definidos, se crea un usuario administrador al arrancar (si no existe).
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
