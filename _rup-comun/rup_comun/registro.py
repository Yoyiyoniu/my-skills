"""Comprueba el registro de preguntas y respuestas de un documento."""
import re
from pathlib import Path

NOMBRE = "preguntas-respuestas.md"
SIN_PREGUNTAS = "sin preguntas"


def ruta_por_defecto(entrada_json):
    return Path(entrada_json).parent / NOMBRE


def _seccion(texto, titulo):
    """Devuelve el cuerpo de `## titulo`, o None si no existe."""
    m = re.search(rf"^## {re.escape(titulo)}[ \t]*$", texto, re.M | re.I)
    if m is None:
        return None
    fin = re.compile(r"^## ", re.M).search(texto, m.end())
    return texto[m.end():fin.start() if fin else len(texto)]


def _tiene_respuestas(cuerpo):
    filas = [f for f in cuerpo.splitlines() if re.match(r"^\|\s*\d", f)]
    return bool(filas) or SIN_PREGUNTAS in cuerpo.lower()


def problemas(ruta, titulo):
    """Devuelve lo que falta en el registro para el documento `titulo`."""
    ruta = Path(ruta)
    if not ruta.is_file():
        return [f"Falta el registro de preguntas y respuestas: {ruta}"]
    cuerpo = _seccion(ruta.read_text(encoding="utf-8"), titulo)
    if cuerpo is None:
        return [f"El registro {ruta} no tiene la sección «## {titulo}»"]
    if not _tiene_respuestas(cuerpo):
        return [f"La sección «## {titulo}» de {ruta} no tiene respuestas ni indica «Sin preguntas»"]
    return []
