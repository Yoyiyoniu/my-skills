"""Render a PDF con LibreOffice y búsqueda de páginas con pdftotext."""
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

HERRAMIENTAS = {
    "soffice": "LibreOffice (soffice). Instálalo, por ejemplo: sudo pacman -S libreoffice-fresh",
    "pdftotext": "pdftotext (poppler). Instálalo, por ejemplo: sudo pacman -S poppler",
}


class ErrorGeneracion(Exception):
    pass


@dataclass
class Entrada:
    """Una línea del índice."""
    numero: str
    titulo: str
    nivel: int
    ancla: str = ""


def requerir_herramientas():
    faltan = [d for h, d in HERRAMIENTAS.items() if shutil.which(h) is None]
    if faltan:
        raise ErrorGeneracion("Falta una herramienta necesaria: " + "; ".join(faltan))


def a_pdf(ruta, carpeta):
    """Convierte `ruta` a PDF en `carpeta`, con un perfil propio para no chocar con una sesión abierta."""
    ruta, carpeta = Path(ruta), Path(carpeta)
    with tempfile.TemporaryDirectory(prefix="rup-lo-") as perfil:
        r = subprocess.run(
            ["soffice", f"-env:UserInstallation=file://{perfil}", "--headless",
             "--convert-to", "pdf", "--outdir", str(carpeta), str(ruta)],
            capture_output=True, text=True, timeout=180,
        )
    pdf = carpeta / (ruta.stem + ".pdf")
    if r.returncode != 0 or not pdf.exists():
        raise ErrorGeneracion(f"LibreOffice no pudo renderizar {ruta.name}: {(r.stderr or r.stdout).strip()}")
    return pdf


def paginas_texto(pdf):
    r = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise ErrorGeneracion(f"pdftotext falló: {r.stderr.strip()}")
    return r.stdout.split("\f")[:-1]


def _es_linea_de_indice(linea):
    return re.search(r"(\.{3,}|\s{2,})\s*\d+\s*$", linea) is not None


def localizar(entradas, paginas):
    """Devuelve {ancla: página}. Los títulos se buscan en orden para tolerar repetidos."""
    resultado, pagina, linea = {}, 0, 0
    for e in entradas:
        numero = re.escape(e.numero.rstrip("."))
        # Se compara el inicio del título porque uno largo puede partirse en dos líneas.
        inicio = re.escape(" ".join(e.titulo.split())[:40])
        patron = re.compile(rf"^\s*{numero}\.?\s+{inicio}")
        encontrado = False
        for p in range(pagina, len(paginas)):
            lineas = paginas[p].splitlines()
            for i in range(linea if p == pagina else 0, len(lineas)):
                normal = re.sub(r"\s+", " ", lineas[i])
                if patron.match(normal) and not _es_linea_de_indice(lineas[i]):
                    resultado[e.ancla] = p + 1
                    pagina, linea, encontrado = p, i + 1, True
                    break
            if encontrado:
                break
        if not encontrado:
            raise ErrorGeneracion(f"No se encontró el título «{e.numero} {e.titulo}» en el PDF")
    return resultado
