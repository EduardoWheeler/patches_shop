# Patches Shop

Tienda de parches personalizados: FastAPI + SQLAlchemy + MySQL + Vanilla JS.

## Puesta en marcha

1. Crea la base de datos: `mysql -u root -p < schema.sql` (opcional: las tablas también se crean al arrancar).
2. `python -m venv venv && source venv/bin/activate` (en Windows: `venv\Scripts\activate`)
3. `pip install -r requirements.txt`
4. Exporta la conexión: `export DATABASE_URL="mysql+pymysql://usuario:clave@localhost:3306/patches_db"`
5. `uvicorn app.main:app --reload`

Tienda: http://localhost:8000 — Documentación de la API: http://localhost:8000/docs

Al primer arranque se cargan categorías y productos de ejemplo.



## Autenticación y migraciones (Bloque 1)

- Las tablas ahora se gestionan con Alembic (`schema.sql` queda como referencia).
  - Base de datos nueva: `alembic upgrade head`
  - Base de datos ya creada con la versión anterior: `alembic stamp 0001 && alembic upgrade head`
  - Tras cambiar un modelo: `alembic revision --autogenerate -m "descripcion"` y luego `alembic upgrade head`
- Define `SECRET_KEY`, `ADMIN_EMAIL` y `ADMIN_PASSWORD` (ver `.env.example`). El admin se crea al arrancar.
- `POST /api/auth/login` devuelve un token; envíalo como `Authorization: Bearer <token>`.
- Rutas protegidas (rol admin): crear/editar/borrar productos, crear categorías y consultar o actualizar pedidos.
  El catálogo público y `POST /api/orders` siguen abiertos.



## Panel de administración (Bloque 2)

- Entra en http://localhost:8000/admin con el usuario definido en `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
- Gestión de productos (con subida de imagen), categorías y pedidos.
- Las imágenes se guardan en `app/static/uploads/` (PNG, JPG o WEBP, máx. 2 MB, validadas por contenido).
- Cancelar un pedido repone el stock automáticamente; un pedido cancelado no puede reabrirse.
- Tras actualizar: `pip install -r requirements.txt` y `alembic upgrade head` (migración `0003`).

## Tests (Bloque 3)

- `pip install -r requirements-dev.txt`
- `pytest` (usa SQLite en memoria: no necesita MySQL ni variables de entorno).
- Cubren autenticación y permisos, catálogo, pedidos (stock, rollback, cancelación) y subida de imágenes.
