#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-docx", "lxml"]
# ///
"""Imprime el texto de un .docx con sus números de lista, sin usar LibreOffice."""
import sys
from collections import defaultdict

import docx
from docx.oxml.ns import qn


def _formatos(doc):
    """Devuelve {(numId, nivel): (formato, plantilla)} desde numbering.xml."""
    try:
        numeracion = doc.part.numbering_part.element
    except (KeyError, NotImplementedError):
        return {}
    abstractos = {a.get(qn("w:abstractNumId")): a for a in numeracion.findall(qn("w:abstractNum"))}
    formatos = {}
    for num in numeracion.findall(qn("w:num")):
        abstracto = abstractos.get(num.find(qn("w:abstractNumId")).get(qn("w:val")))
        if abstracto is None:
            continue
        for lvl in abstracto.findall(qn("w:lvl")):
            formato, plantilla = lvl.find(qn("w:numFmt")), lvl.find(qn("w:lvlText"))
            formatos[(num.get(qn("w:numId")), int(lvl.get(qn("w:ilvl"))))] = (
                formato.get(qn("w:val")) if formato is not None else "decimal",
                plantilla.get(qn("w:val")) if plantilla is not None else "",
            )
    return formatos


def _valor(n, formato):
    if formato in ("lowerLetter", "upperLetter"):
        letra = chr(ord("a") + (n - 1) % 26)
        return letra if formato == "lowerLetter" else letra.upper()
    return str(n)


class Numerador:
    def __init__(self, doc):
        self.formatos = _formatos(doc)
        self.cuentas = defaultdict(lambda: defaultdict(int))

    def etiqueta(self, parrafo):
        numpr = parrafo.find(f"{qn('w:pPr')}/{qn('w:numPr')}")
        if numpr is None or numpr.find(qn("w:numId")) is None:
            return "", 0
        num_id = numpr.find(qn("w:numId")).get(qn("w:val"))
        ilvl = numpr.find(qn("w:ilvl"))
        nivel = int(ilvl.get(qn("w:val"))) if ilvl is not None else 0
        formato, plantilla = self.formatos.get((num_id, nivel), ("bullet", ""))
        if formato in ("bullet", "none"):
            return "-", nivel
        cuentas = self.cuentas[num_id]
        cuentas[nivel] += 1
        for inferior in [k for k in cuentas if k > nivel]:
            del cuentas[inferior]
        texto = plantilla
        for i in range(nivel + 1):
            texto = texto.replace(f"%{i + 1}", _valor(cuentas[i] or 1, self.formatos.get((num_id, i), ("decimal", ""))[0]))
        return texto, nivel


def _texto(parrafo):
    return "".join(t.text or "" for t in parrafo.iter(qn("w:t"))).strip()


def lineas(ruta):
    """Devuelve el cuerpo en orden: párrafos y tablas. Omite el índice, que repite los títulos."""
    doc = docx.Document(str(ruta))
    numerador = Numerador(doc)
    resultado = []
    for el in doc.element.body:
        if el.tag == qn("w:tbl"):
            for fila in el.findall(qn("w:tr")):
                celdas = [" ".join(_texto(p) for p in c.iter(qn("w:p"))).strip() for c in fila.findall(qn("w:tc"))]
                resultado.append(" | ".join(celdas))
        elif el.tag == qn("w:p"):
            texto = _texto(el)
            if texto:
                etiqueta, nivel = numerador.etiqueta(el)
                resultado.append("  " * nivel + (f"{etiqueta} {texto}" if etiqueta else texto))
    return resultado


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: leer_docx.py <archivo.docx>")
    print("\n".join(lineas(sys.argv[1])))
