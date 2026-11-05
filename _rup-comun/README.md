# _rup-comun

Código y reglas que comparten `rup-caso-de-uso`, `rup-especificacion-suplementaria` y `rup-glosario`. No es una skill: no tiene `SKILL.md`. Si mueves las skills a otra carpeta, mueve esta con ellas.

- `rup_comun/`: validación del JSON, lint, render, índice y escritura segura.
- `leer_docx.py`: imprime el texto de un `.docx` con sus números de lista, sin LibreOffice.
- `reglas-comunes.md`: fuentes, reglas comunes, conflictos y lo que no se pudo verificar.
- `redaccion-humanizada.md`: cómo usar `humanizer` en estos documentos.

Para ejecutar las pruebas, desde esta carpeta:

```bash
uv run --with pytest --with python-docx --with lxml python -m pytest tests -q -p no:cacheprovider
```
