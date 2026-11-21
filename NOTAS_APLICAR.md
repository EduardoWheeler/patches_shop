# Cambios a aplicar en patchesshop

- Reemplaza `app/config.py`, `schema.sql` y `.env.example` por los de esta carpeta.
- Agrega `python-dotenv>=1.0` a `requirements.txt`.
- **Borra** `apply_block1.py`, `apply_block2.py`, `apply_block3.py` y `generate_project.py`
  (o muévelos fuera del repo): son andamiaje y pueden sobrescribir archivos del proyecto.
- `DATABASE_URL` ahora es obligatoria. Los tests ya la definen en `tests/conftest.py`, así que siguen funcionando.
