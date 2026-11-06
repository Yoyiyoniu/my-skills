"""Carga y validación del JSON de entrada."""
import json
import re
from pathlib import Path

PENDIENTE = re.compile(r"\[PENDIENTE:[^\]]*\]")
FECHA = re.compile(r"^\d{1,2}/[A-Za-zÁÉÍÓÚáéíóúñÑ]+/(\d{4})$")


class ErrorEntrada(Exception):
    """El JSON no se puede usar. `errores` trae un mensaje por problema."""

    def __init__(self, errores):
        super().__init__("\n".join(errores))
        self.errores = list(errores)


class Opcional:
    def __init__(self, esquema):
        self.esquema = esquema


ESQUEMA_BASE = {
    "proyecto": {"nombre": str, "empresa": str, "organizacion": str, "identificador": str},
    "documento": {"version": str, "fecha": str},
    "historial": [{"fecha": str, "version": str, "descripcion": str, "autor": str}],
    "redaccion": Opcional({"humanizer_aplicado": bool, "revision_confirmada": Opcional(bool)}),
}

_NOMBRES = {str: "texto", int: "número entero", bool: "booleano"}


def cargar(ruta):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ErrorEntrada([f"No existe el archivo de entrada: {ruta}"]) from None
    except json.JSONDecodeError as e:
        raise ErrorEntrada([f"JSON inválido en {ruta}: línea {e.lineno}, {e.msg}"]) from None


def validar_esquema(valor, esquema, ruta=""):
    """Devuelve un error por cada campo ausente o de tipo incorrecto."""
    if isinstance(esquema, Opcional):
        return validar_esquema(valor, esquema.esquema, ruta)
    if isinstance(esquema, dict):
        if not isinstance(valor, dict):
            return [f"{ruta}: debe ser un objeto"]
        errores = []
        for clave, sub in esquema.items():
            hijo = f"{ruta}.{clave}" if ruta else clave
            if clave not in valor:
                if not isinstance(sub, Opcional):
                    errores.append(f"{hijo}: campo obligatorio ausente")
                continue
            errores += validar_esquema(valor[clave], sub, hijo)
        return errores
    if isinstance(esquema, list):
        if not isinstance(valor, list):
            return [f"{ruta}: debe ser una lista"]
        errores = []
        for i, item in enumerate(valor):
            errores += validar_esquema(item, esquema[0], f"{ruta}[{i}]")
        return errores
    # bool es subclase de int: se descarta para no aceptar true como número.
    if not isinstance(valor, esquema) or (esquema is int and isinstance(valor, bool)):
        return [f"{ruta}: debe ser {_NOMBRES[esquema]}"]
    if esquema is str and not valor.strip():
        return [f"{ruta}: no puede estar vacío"]
    return []


def validar_base(datos):
    """Comprueba fecha, historial y coherencia de versión."""
    errores = []
    fecha = datos["documento"]["fecha"]
    if not PENDIENTE.search(fecha) and not FECHA.match(fecha):
        errores.append(f"documento.fecha: '{fecha}' no tiene la forma dd/Mes/aaaa")
    historial = datos["historial"]
    if not historial:
        errores.append("historial: debe tener al menos una revisión")
    elif historial[-1]["version"] != datos["documento"]["version"]:
        errores.append(
            f"historial: la última revisión es {historial[-1]['version']} "
            f"y documento.version es {datos['documento']['version']}"
        )
    return errores


def anio(datos):
    m = FECHA.match(datos["documento"]["fecha"])
    return m.group(1) if m else "[PENDIENTE: año]"


def recorrer_textos(valor, ruta=""):
    """Produce (ruta, texto) por cada cadena del JSON."""
    if isinstance(valor, str):
        yield ruta, valor
    elif isinstance(valor, dict):
        for k, v in valor.items():
            yield from recorrer_textos(v, f"{ruta}.{k}" if ruta else k)
    elif isinstance(valor, list):
        for i, v in enumerate(valor):
            yield from recorrer_textos(v, f"{ruta}[{i}]")


def pendientes(datos):
    return [(r, m) for r, t in recorrer_textos(datos) for m in PENDIENTE.findall(t)]


def revision_confirmada(datos):
    return datos.get("redaccion", {}).get("revision_confirmada") is True


def humanizer_declarado(datos):
    return datos.get("redaccion", {}).get("humanizer_aplicado") is True
