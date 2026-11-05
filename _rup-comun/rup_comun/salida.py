"""Escritura segura del documento final."""
import os
import shutil
from pathlib import Path

from .render import ErrorGeneracion


def comprobar_destino(destino, sobrescribir):
    if Path(destino).exists() and not sobrescribir:
        raise ErrorGeneracion(f"Ya existe {destino}. Usa --sobrescribir para reemplazarlo.")


def mover(origen, destino):
    """Copia junto al destino y renombra: el destino nunca queda a medias."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_name(f".{destino.name}.tmp")
    try:
        shutil.copyfile(origen, temporal)
        os.replace(temporal, destino)
    finally:
        temporal.unlink(missing_ok=True)
