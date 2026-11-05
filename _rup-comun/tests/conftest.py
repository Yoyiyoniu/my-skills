import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS / "_rup-comun"))


def cargar_generador(skill):
    ruta = SKILLS / skill / "scripts" / "generar.py"
    spec = importlib.util.spec_from_file_location(skill.replace("-", "_"), ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def ejemplo(skill):
    return json.loads((SKILLS / skill / "assets" / "ejemplo.json").read_text(encoding="utf-8"))


def limpiar_pendientes(datos):
    """Convierte un ejemplo en una versión final válida."""
    texto = json.dumps(datos, ensure_ascii=False)
    import re
    texto = re.sub(r"\[PENDIENTE:[^\]]*\]", "Valor de prueba", texto)
    d = json.loads(texto)
    d["redaccion"] = {"humanizer_aplicado": True}
    return d


@pytest.fixture(scope="session")
def uc():
    return cargar_generador("rup-caso-de-uso")


@pytest.fixture(scope="session")
def supl():
    return cargar_generador("rup-especificacion-suplementaria")


@pytest.fixture(scope="session")
def glos():
    return cargar_generador("rup-glosario")


@pytest.fixture
def datos_uc():
    return copy.deepcopy(ejemplo("rup-caso-de-uso"))


@pytest.fixture
def datos_supl():
    return copy.deepcopy(ejemplo("rup-especificacion-suplementaria"))


@pytest.fixture
def datos_glos():
    return copy.deepcopy(ejemplo("rup-glosario"))


def escribir(tmp_path, datos, nombre="entrada.json"):
    ruta = tmp_path / nombre
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return str(ruta)
