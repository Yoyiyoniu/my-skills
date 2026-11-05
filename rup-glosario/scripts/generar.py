#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["lxml"]
# ///
"""Genera el Glosario sobre la plantilla RUP en formato OpenDocument."""
import copy
import re
import sys
import unicodedata
import uuid
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_rup-comun"))

from lxml import etree  # noqa: E402

from rup_comun import cli, entrada, verificar  # noqa: E402
from rup_comun.entrada import Opcional  # noqa: E402
from rup_comun.lint import AVISA, BLOQUEA, Campo, Hallazgo, Regla  # noqa: E402
from rup_comun.render import Entrada, ErrorGeneracion  # noqa: E402

PLANTILLA = Path(__file__).resolve().parents[1] / "assets" / "plantilla.odt"
TITULO = "Glosario"

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
    "dc": "http://purl.org/dc/elements/1.1/",
    "meta": "urn:oasis:names:tc:opendocument:xmlns:meta:1.0",
    "manifest": "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0",
}
TEXT = f"{{{NS['text']}}}"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"

# Textos que identifican cada pieza de la plantilla. Una prueba falla si alguno desaparece.
T_PROYECTO = "<Project Name>"
T_PORTADA = "Glossary"
T_VERSION = "Version <1.0>"
T_HISTORIAL = "Revision History"
T_INDICE = "Table of Contents"
T_PRIMER_TITULO = "Introduction"
T_H1 = "Definitions"
T_H2 = "<aTerm>"
T_H3 = "<aGroupTerm>"
T_CUERPO = "[Specify the purpose of this Glossary.]"
INICIO_GUIA_PORTADA = ("[Note:", "[To customize")
PIEZAS = (T_PROYECTO, T_PORTADA, T_VERSION, T_HISTORIAL, T_INDICE, T_PRIMER_TITULO, T_H1, T_H2, T_H3, T_CUERPO)
ESTILO_TEXTO = "T10"
ESTILO_TAB_INDICE = "T11"

TERMINO = {"termino": str, "definicion": str}
ESQUEMA = {
    "introduccion": {"proposito": str, "alcance": str, "referencias": [str], "descripcion_general": str},
    "terminos": [TERMINO],
    "grupos": [{"nombre": str, "descripcion": str, "terminos": [TERMINO]}],
    "estereotipos": [{"nombre": str, "significado": str}],
}

DEF = ("definicion",)
REGLAS = [
    Regla("G1-APERTURA", r"^\s*(?:es cuando|se refiere a|es un término|es una palabra|significa que|término que)\b",
          AVISA, "Empieza por la categoría del término y sus rasgos.", DEF),
    Regla("G-NEGATIVA", r"^\s*(?:no es\b|lo que no\b|aquello que no\b)", AVISA,
          "Definición negativa: di qué es el término.", DEF),
]


def clave_orden(texto):
    """Orden alfabético del español: sin mayúsculas ni acentos, y la ñ después de la n."""
    t = unicodedata.normalize("NFC", texto).casefold().replace("ñ", "n~")
    return "".join(ch for ch in unicodedata.normalize("NFD", t) if unicodedata.category(ch) != "Mn")


def sin_acentos(texto):
    return "".join(ch for ch in unicodedata.normalize("NFD", texto.casefold()) if unicodedata.category(ch) != "Mn")


def todos_los_terminos(c):
    """Produce (ruta, término)."""
    for i, t in enumerate(c["terminos"]):
        yield f"contenido.terminos[{i}]", t
    for g, grupo in enumerate(c["grupos"]):
        for i, t in enumerate(grupo["terminos"]):
            yield f"contenido.grupos[{g}].terminos[{i}]", t


def validar(datos):
    c = datos["contenido"]
    errores, vistos = [], {}
    for ruta, t in todos_los_terminos(c):
        clave = sin_acentos(t["termino"])
        if clave in vistos:
            errores.append(f"{ruta}: término repetido «{t['termino']}», ya definido en {vistos[clave]}")
        vistos.setdefault(clave, ruta)
    if not vistos:
        errores.append("contenido.terminos: el glosario debe definir al menos un término")
    for g, grupo in enumerate(c["grupos"]):
        if not grupo["terminos"]:
            errores.append(f"contenido.grupos[{g}]: el grupo «{grupo['nombre']}» no tiene términos")
    return errores


def campos(datos):
    c = datos["contenido"]
    i = c["introduccion"]
    lista = [Campo(f"contenido.introduccion.{k}", i[k]) for k in ("proposito", "alcance", "descripcion_general")]
    lista += [Campo(f"{r}.definicion", t["definicion"], "definicion") for r, t in todos_los_terminos(c)]
    lista += [Campo(f"contenido.grupos[{n}].descripcion", g["descripcion"]) for n, g in enumerate(c["grupos"])]
    lista += [Campo(f"contenido.estereotipos[{n}].significado", e["significado"])
              for n, e in enumerate(c["estereotipos"])]
    return lista


def _menciona(definicion, termino):
    return re.search(rf"\b{re.escape(sin_acentos(termino))}\b", sin_acentos(definicion)) is not None


def lint_extra(datos):
    terminos = [(r, t) for r, t in todos_los_terminos(datos["contenido"])
                if not entrada.PENDIENTE.search(t["definicion"])]
    hallazgos = []
    for r, t in terminos:
        ruta = f"{r}.definicion"
        if _menciona(t["definicion"], t["termino"]):
            hallazgos.append(Hallazgo(ruta, t["termino"], "G-CIRCULAR",
                                      "La definición repite el término y no lo explica.", AVISA))
        if "\n" in t["definicion"].strip():
            hallazgos.append(Hallazgo(ruta, t["termino"], "G6", "La definición ocupa más de un párrafo.", BLOQUEA))
    for i, (r, a) in enumerate(terminos):
        for _, b in terminos[i + 1:]:
            if _menciona(a["definicion"], b["termino"]) and _menciona(b["definicion"], a["termino"]):
                hallazgos.append(Hallazgo(f"{r}.definicion", f"{a['termino']} / {b['termino']}", "G-MUTUA",
                                          "Los dos términos se definen entre sí: revisa si son circulares.", AVISA))
    return hallazgos


def texto_de(el):
    return "".join(el.itertext())


def poner_texto(parrafo, texto, estilo=None):
    """Deja `texto` en el primer span del párrafo y borra el resto."""
    spans = parrafo.findall(f"{TEXT}span")
    if spans:
        span = spans[0]
        estilo = estilo or span.get(f"{TEXT}style-name")
    else:
        span = etree.SubElement(parrafo, f"{TEXT}span")
    for hijo in list(parrafo):
        if hijo is not span:
            parrafo.remove(hijo)
    for hijo in list(span):
        span.remove(hijo)
    parrafo.text = None
    span.text = texto
    span.tail = None
    if estilo:
        span.set(f"{TEXT}style-name", estilo)


def _span(padre, estilo, texto=None):
    s = etree.SubElement(padre, f"{TEXT}span")
    s.set(f"{TEXT}style-name", estilo)
    s.text = texto
    return s


class Glosario:
    """Documento construido, con la interfaz que espera el flujo común."""

    def __init__(self, datos):
        self.datos = datos
        with zipfile.ZipFile(PLANTILLA) as z:
            self.archivos = {i.filename: z.read(i.filename) for i in z.infolist() if not i.is_dir()}
        self.content = etree.fromstring(self.archivos["content.xml"])
        self.styles = etree.fromstring(self.archivos["styles.xml"])
        self.meta = etree.fromstring(self.archivos["meta.xml"])
        self.texto = self.content.find(".//office:text", NS)
        self.hijos = list(self.texto)
        self.indice = []
        self._tabs = {}
        self._contadores = [0, 0, 0]

    def _buscar(self, texto, inicio=0):
        for el in self.hijos[inicio:]:
            if texto_de(el).strip() == texto:
                return el
        raise ErrorGeneracion(f"La plantilla no contiene la pieza «{texto}»")

    def construir(self):
        proyecto, documento = self.datos["proyecto"], self.datos["documento"]
        poner_texto(self._buscar(T_PROYECTO), proyecto["nombre"])
        poner_texto(self._buscar(T_PORTADA), TITULO)
        poner_texto(self._buscar(T_VERSION), f"Versión {documento['version']}")
        poner_texto(self._buscar(T_HISTORIAL), "Historial de revisiones")
        poner_texto(self._buscar(T_INDICE), "Índice")
        self._historial()

        primero = self._buscar(T_PRIMER_TITULO)
        inicio = self.hijos.index(primero)
        self.titulo_cuerpo = self.hijos[inicio - 1]
        poner_texto(self.titulo_cuerpo, TITULO)
        self.prototipos = {
            "primero": copy.deepcopy(primero),
            1: copy.deepcopy(self._buscar(T_H1)),
            2: copy.deepcopy(self._buscar(T_H2)),
            3: copy.deepcopy(self._buscar(T_H3)),
        }
        self.modelo_cuerpo = copy.deepcopy(self._buscar(T_CUERPO))
        self._indice_modelos()

        for el in self.hijos[:inicio]:
            if el.tag == f"{TEXT}p" and texto_de(el).startswith(INICIO_GUIA_PORTADA):
                self.texto.remove(el)
        ultimo = self.hijos[-1]
        for el in self.hijos[inicio:-1]:
            self.texto.remove(el)
        self.fin = ultimo
        self._cuerpo()
        self._escribir_indice()
        self._encabezados()
        self._idioma()
        self._metadatos()

    def _historial(self):
        tabla = self.texto.find("table:table", NS)
        for celda, valor in zip(tabla.findall("table:table-row", NS)[0].findall("table:table-cell", NS),
                                ("Fecha", "Versión", "Descripción", "Autor")):
            poner_texto(celda.find("text:p", NS), valor)
        filas = tabla.findall("table:table-row", NS)
        modelo = filas[1]
        for f in filas[1:]:
            tabla.remove(f)
        for r in self.datos["historial"]:
            fila = copy.deepcopy(modelo)
            for celda, valor in zip(fila.findall("table:table-cell", NS),
                                    (r["fecha"], r["version"], r["descripcion"], r["autor"])):
                poner_texto(celda.find("text:p", NS), valor)
            tabla.append(fila)

    def _indice_modelos(self):
        cuerpo_indice = self.content.find(".//text:index-body", NS)
        self.indice_cuerpo = cuerpo_indice
        self.indice_estilos = {}
        for p in cuerpo_indice.findall("text:p", NS):
            m = re.match(r"\s*(\d+(?:\.\d+)*)", texto_de(p))
            if m:
                self.indice_estilos.setdefault(m.group(1).count(".") + 1, p.get(f"{TEXT}style-name"))
        self._alinear_paginas_indice()

    def _alinear_paginas_indice(self):
        """Cada nivel de la plantilla tiene otro margen derecho: los números quedan desalineados."""
        estilos = self.content.find("office:automatic-styles", NS)
        for nombre in self.indice_estilos.values():
            props = estilos.find(f"style:style[@style:name='{nombre}']", NS).find("style:paragraph-properties", NS)
            props.set(f"{{{NS['fo']}}}margin-right", "0in")

    def _agregar(self, el):
        self.fin.addprevious(el)

    def _titulo(self, nivel, texto, primero=False):
        self._contadores[nivel - 1] += 1
        self._contadores[nivel:] = [0] * (3 - nivel)
        lista = copy.deepcopy(self.prototipos["primero" if primero else nivel])
        for el in lista.iter(f"{TEXT}list"):
            if el.get(XML_ID):
                el.set(XML_ID, f"list{uuid.uuid4().int % 10**15}")
        parrafos = list(lista.iter(f"{TEXT}p"))
        for b in lista.iter(f"{TEXT}bookmark"):
            b.getparent().remove(b)
        poner_texto(parrafos[0], texto)
        self._agregar(lista)
        partes = [str(c) for c in self._contadores[:nivel]]
        numero = partes[0] + "." if nivel == 1 else ".".join(partes)
        self.indice.append(Entrada(numero, " ".join(texto.split()), nivel, f"e{len(self.indice)}"))

    def _parrafo(self, texto):
        p = copy.deepcopy(self.modelo_cuerpo)
        poner_texto(p, texto, ESTILO_TEXTO)
        self._agregar(p)

    def _cuerpo(self):
        c = self.datos["contenido"]
        i = c["introduccion"]
        self._titulo(1, "Introducción", primero=True)
        self._titulo(2, "Propósito")
        self._parrafo(i["proposito"])
        self._titulo(2, "Alcance")
        self._parrafo(i["alcance"])
        self._titulo(2, "Referencias")
        for r in i["referencias"] or ["Este documento no cita referencias."]:
            self._parrafo(r)
        self._titulo(2, "Descripción general")
        self._parrafo(i["descripcion_general"])
        self._titulo(1, "Definiciones")
        for t in sorted(c["terminos"], key=lambda x: clave_orden(x["termino"])):
            self._titulo(2, t["termino"])
            self._parrafo(t["definicion"])
        for g in sorted(c["grupos"], key=lambda x: clave_orden(x["nombre"])):
            self._titulo(2, g["nombre"])
            self._parrafo(g["descripcion"])
            for t in sorted(g["terminos"], key=lambda x: clave_orden(x["termino"])):
                self._titulo(3, t["termino"])
                self._parrafo(t["definicion"])
        self._titulo(1, "Estereotipos UML")
        if not c["estereotipos"]:
            self._parrafo("No se definieron estereotipos adicionales.")
        for e in c["estereotipos"]:
            self._parrafo(f"«{e['nombre']}»: {e['significado']}")

    def _escribir_indice(self):
        for p in self.indice_cuerpo.findall("text:p", NS):
            self.indice_cuerpo.remove(p)
        for e in self.indice:
            p = etree.SubElement(self.indice_cuerpo, f"{TEXT}p")
            p.set(f"{TEXT}style-name", self.indice_estilos[e.nivel])
            _span(p, ESTILO_TEXTO, e.numero)
            etree.SubElement(_span(p, ESTILO_TAB_INDICE), f"{TEXT}tab")
            titulo = _span(p, ESTILO_TEXTO, e.titulo)
            tab = etree.SubElement(titulo, f"{TEXT}tab")
            tab.tail = "0"
            self._tabs[e.ancla] = tab

    def poner_paginas(self, paginas):
        for ancla, numero in paginas.items():
            self._tabs[ancla].tail = str(numero)

    def _encabezados(self):
        proyecto, documento = self.datos["proyecto"], self.datos["documento"]
        for maestra in self.styles.iterfind(".//style:master-page", NS):
            for parte, valor in (("header", proyecto["empresa"]), ("footer", proyecto["organizacion"])):
                zona = maestra.find(f"style:{parte}", NS)
                if zona is None:
                    continue
                # Un campo Company se recalcula al abrir: mostraría el mismo valor en ambos sitios.
                for campo in list(zona.iter(f"{TEXT}user-defined")):
                    campo.text = None
                    campo.tag = f"{TEXT}span"
                    for atributo in list(campo.attrib):
                        del campo.attrib[atributo]
                    campo.text = valor
                for p in zona.iter(f"{TEXT}p"):
                    t = texto_de(p)
                    if "<Project Name>" in t:
                        poner_texto(p, proyecto["nombre"])
                    elif "Version:" in t:
                        poner_texto(p, f"Versión: {documento['version']}")
                    elif "Date:" in t:
                        poner_texto(p, f"Fecha: {documento['fecha']}")
                    elif "<document identifier>" in t:
                        poner_texto(p, proyecto["identificador"])
                    elif t.strip() == "Glossary":
                        poner_texto(p, TITULO)
                    elif t.strip() == "Confidential":
                        poner_texto(p, "Confidencial")
                    else:
                        for s in p.iter(f"{TEXT}span"):
                            if s.text and ", 2001" in s.text:
                                s.text = s.text.replace(", 2001", f", {entrada.anio(self.datos)}")
                            elif s.text == "Page ":
                                s.text = "Página "

    def _idioma(self):
        idioma, pais = f"{{{NS['fo']}}}language", f"{{{NS['fo']}}}country"
        for raiz in (self.styles, self.content):
            for el in raiz.iter():
                if el.get(idioma):
                    el.set(idioma, "es")
                    el.set(pais, "MX")

    def _metadatos(self):
        proyecto = self.datos["proyecto"]
        office = self.meta.find("office:meta", NS)
        valores = (("dc:title", TITULO), ("dc:subject", proyecto["nombre"]), ("dc:creator", proyecto["organizacion"]),
                   ("meta:initial-creator", proyecto["organizacion"]))
        for etiqueta, valor in valores:
            el = office.find(etiqueta, NS)
            if el is None:
                prefijo, local = etiqueta.split(":")
                el = etree.SubElement(office, f"{{{NS[prefijo]}}}{local}")
            el.text = valor
        for el in office.findall("meta:user-defined", NS):
            if el.get(f"{{{NS['meta']}}}name") == "Company":
                el.text = proyecto["empresa"]

    def guardar(self, ruta):
        partes = dict(self.archivos)
        partes.pop("Thumbnails/thumbnail.png", None)  # miniatura de la plantilla en blanco
        manifiesto = etree.fromstring(partes["META-INF/manifest.xml"])
        ruta_attr = f"{{{NS['manifest']}}}full-path"
        for entrada_m in list(manifiesto):
            if entrada_m.get(ruta_attr, "").startswith("Thumbnails"):
                manifiesto.remove(entrada_m)

        def xml(raiz):
            return etree.tostring(raiz, xml_declaration=True, encoding="UTF-8")

        partes.update({"content.xml": xml(self.content), "styles.xml": xml(self.styles), "meta.xml": xml(self.meta),
                       "META-INF/manifest.xml": xml(manifiesto)})
        with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
            # ODF exige que mimetype sea la primera entrada y vaya sin comprimir.
            z.writestr(zipfile.ZipInfo("mimetype"), partes.pop("mimetype"), compress_type=zipfile.ZIP_STORED)
            for nombre, contenido in partes.items():
                z.writestr(nombre, contenido)


def construir(datos):
    g = Glosario(datos)
    g.construir()
    return g


TIPO = cli.TipoDocumento(
    descripcion=__doc__,
    extension=".odt",
    esquema_contenido=ESQUEMA,
    validar=validar,
    campos=campos,
    reglas=REGLAS,
    lint_extra=lint_extra,
    construir=construir,
    salida_por_defecto=lambda d: Path("docs") / "Glosario.odt",
    textos=verificar.textos_odt,
    guias=verificar.guias_de(verificar.textos_odt(PLANTILLA)) + ["The definition for"],
    etiquetas_en=[
        r"\bGlossary\b", r"\bRevision History\b", r"\bTable of Contents\b", r"\bIntroduction\b", r"\bPurpose\b",
        r"\bScope\b", r"\bReferences\b", r"\bOverview\b", r"\bDefinitions\b", r"\bUML Stereotypes\b",
        r"\bConfidential\b", r"\bDate\b", r"\bVersion\b", r"\bPage\b", r"\bDescription\b", r"\bAuthor\b",
        r"\bCompany\b", r", 2001\b",
    ],
)

if __name__ == "__main__":
    sys.exit(cli.ejecutar(TIPO))
