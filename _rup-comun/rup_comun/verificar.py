"""Verificación del documento ya generado."""
import re
import zipfile
from html import unescape

from .entrada import PENDIENTE

MARCADOR = re.compile(r"<[^<>]{1,80}>")


def _parrafos(xml, etiqueta):
    for bloque in re.findall(rf"<{etiqueta}[ >].*?</{etiqueta}>", xml, re.S):
        texto = unescape(re.sub(r"<[^>]+>", "", bloque)).strip()
        if texto:
            yield texto


def textos_docx(ruta):
    with zipfile.ZipFile(ruta) as z:
        partes = [n for n in z.namelist() if re.match(r"word/(document|header\d*|footer\d*)\.xml$", n)]
        return [t for n in partes for t in _parrafos(z.read(n).decode("utf-8"), "w:p")]


def textos_odt(ruta):
    with zipfile.ZipFile(ruta) as z:
        return [t for n in ("content.xml", "styles.xml") for t in _parrafos(z.read(n).decode("utf-8"), "text:p")]


def guias_de(textos):
    """Texto guía de una plantilla: párrafos entre corchetes."""
    return [t for t in textos if t.startswith("[") and len(t) > 12]


def comprobar(textos, guias, etiquetas_en, permitir_pendientes=False):
    """Devuelve un problema por cada resto de plantilla en `textos`."""
    problemas = []
    guias = [g[:60] for g in guias]
    for texto in textos:
        limpio = PENDIENTE.sub("", texto) if permitir_pendientes else texto
        for g in guias:
            if g in limpio:
                problemas.append(f"Texto guía de la plantilla: «{g}»")
        m = MARCADOR.search(limpio)
        if m:
            problemas.append(f"Marcador de la plantilla sin sustituir: «{m.group(0)}»")
        for patron in etiquetas_en:
            m = re.search(patron, limpio)
            if m:
                problemas.append(f"Etiqueta de la plantilla sin traducir: «{m.group(0)}» en «{texto[:60]}»")
    return sorted(set(problemas))
