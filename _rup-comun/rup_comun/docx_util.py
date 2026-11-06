"""Edición de plantillas .docx conservando su paquete: estilos, encabezados, pies y numeración."""
import copy
import re

from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from .render import Entrada

IDIOMA = "es-MX"


def texto_de(elemento):
    return "".join(t.text or "" for t in elemento.iter(qn("w:t")))


def partes_encabezado_pie(doc):
    """Produce (elemento, es_encabezado) por cada encabezado y pie del documento."""
    for rel in doc.part.rels.values():
        if rel.reltype == RT.HEADER:
            yield rel.target_part.element, True
        elif rel.reltype == RT.FOOTER:
            yield rel.target_part.element, False


def aplanar_campos(elemento, valores):
    """Sustituye por texto fijo los campos cuyo código esté en `valores`.

    Un campo DATE o DOCPROPERTY mostraría otro valor al actualizarse en Word.
    Los demás, como PAGE, se conservan.
    """
    for p in elemento.iter(qn("w:p")):
        campo = None
        for nodo in list(p.iter(qn("w:fldChar"), qn("w:instrText"), qn("w:t"))):
            if nodo.tag == qn("w:fldChar"):
                tipo = nodo.get(qn("w:fldCharType"))
                if tipo == "begin":
                    campo = {"control": [nodo], "codigo": "", "resultado": [], "fase": "codigo"}
                elif campo and tipo == "separate":
                    campo["control"].append(nodo)
                    campo["fase"] = "resultado"
                elif campo and tipo == "end":
                    campo["control"].append(nodo)
                    _resolver_campo(campo, valores)
                    campo = None
            elif campo and nodo.tag == qn("w:instrText"):
                campo["control"].append(nodo)
                campo["codigo"] += nodo.text or ""
            elif campo and campo["fase"] == "resultado":
                campo["resultado"].append(nodo)


def _resolver_campo(campo, valores):
    palabras = campo["codigo"].split()
    if not palabras or palabras[0] not in valores:
        return
    if campo["resultado"]:
        campo["resultado"][0].text = valores[palabras[0]]
        for t in campo["resultado"][1:]:
            t.getparent().remove(t)
    else:
        t = OxmlElement("w:t")
        t.text = valores[palabras[0]]
        campo["control"][0].getparent().addnext(_run_con(t))
    for nodo in campo["control"]:
        nodo.getparent().remove(nodo)


def _run_con(hijo):
    r = OxmlElement("w:r")
    r.append(hijo)
    return r


def reemplazar(elemento, mapa):
    """Reemplaza subcadenas dentro de cada w:t."""
    for t in elemento.iter(qn("w:t")):
        for viejo, nuevo in mapa.items():
            if t.text and viejo in t.text:
                t.text = t.text.replace(viejo, nuevo)
                t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def traducir_exacto(elemento, mapa):
    for t in elemento.iter(qn("w:t")):
        if t.text and t.text.strip() in mapa:
            t.text = mapa[t.text.strip()]


def poner_texto(parrafo, texto):
    """Deja `texto` en el primer run con texto y borra el resto."""
    ts = list(parrafo.iter(qn("w:t")))
    if not ts:
        r = parrafo.find(qn("w:r"))
        t = OxmlElement("w:t")
        if r is None:
            parrafo.append(_run_con(t))
        else:
            r.append(t)
        ts = [t]
    ts[0].text = texto
    ts[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    for t in ts[1:]:
        t.getparent().remove(t)


def llenar_tabla(tabla, filas):
    """Usa la segunda fila como modelo y crea una fila por cada entrada."""
    trs = tabla.findall(qn("w:tr"))
    modelo = trs[1]
    for tr in trs[2:]:
        tabla.remove(tr)
    tabla.remove(modelo)
    for fila in filas:
        tr = copy.deepcopy(modelo)
        for tc, valor in zip(tr.findall(qn("w:tc")), fila):
            poner_texto(tc.find(qn("w:p")), valor)
        tabla.append(tr)


def limpiar_parrafo(parrafo):
    """Quita marcadores y runs vacíos heredados del prototipo."""
    for b in list(parrafo.iter(qn("w:bookmarkStart"), qn("w:bookmarkEnd"))):
        b.getparent().remove(b)
    for r in parrafo.findall(qn("w:r")):
        if r.find(qn("w:t")) is None:
            parrafo.remove(r)


def normalizar_alineacion(doc):
    """Cambia jc end/start por right/left: Word ignora los primeros en modo de compatibilidad."""
    equivalentes = {"end": "right", "start": "left"}
    partes = [doc.element, doc.styles.element] + [p for p, _ in partes_encabezado_pie(doc)]
    for parte in partes:
        for jc in parte.iter(qn("w:jc")):
            valor = jc.get(qn("w:val"))
            jc.set(qn("w:val"), equivalentes.get(valor, valor))


def poner_idioma(doc):
    """Las plantillas declaran inglés: Word marcaría todo el texto como error."""
    estilos = doc.styles.element
    for lang in estilos.iter(qn("w:lang")):
        lang.set(qn("w:val"), IDIOMA)
    if next(estilos.iter(qn("w:lang")), None) is None:
        defecto = estilos.find(qn("w:docDefaults"))
        rpr = defecto.find(f"{qn('w:rPrDefault')}/{qn('w:rPr')}") if defecto is not None else None
        if rpr is not None:
            lang = OxmlElement("w:lang")
            lang.set(qn("w:val"), IDIOMA)
            rpr.append(lang)


def propiedades(doc, titulo, datos):
    core = doc.core_properties
    core.title = titulo
    core.subject = datos["proyecto"]["nombre"]
    core.author = datos["proyecto"]["organizacion"]
    core.last_modified_by = datos["proyecto"]["organizacion"]
    core.comments = ""
    core.language = IDIOMA


class Cuerpo:
    """Escribe el cuerpo clonando prototipos y lleva la numeración para el índice."""

    def __init__(self, doc, primero, prototipos, parrafo, nivel_indice):
        """`primero` es el primer elemento del cuerpo a sustituir."""
        self.doc = doc
        self.prototipos = {n: copy.deepcopy(p) for n, p in prototipos.items()}
        self.parrafo_modelo = copy.deepcopy(parrafo)
        self.nivel_indice = nivel_indice
        self.contadores = [0] * 4
        self.indice = []
        self._marca = 1000
        body = doc.element.body
        hijos = list(body)
        for el in hijos[hijos.index(primero):]:
            if el.tag != qn("w:sectPr"):
                body.remove(el)
        self.fin = body.find(qn("w:sectPr"))

    def _agregar(self, el):
        self.fin.addprevious(el)
        return el

    def titulo(self, nivel, texto):
        self.contadores[nivel - 1] += 1
        self.contadores[nivel:] = [0] * (4 - nivel)
        p = copy.deepcopy(self.prototipos[nivel])
        limpiar_parrafo(p)
        poner_texto(p, texto)
        partes = [str(c) for c in self.contadores[:nivel]]
        numero = partes[0] + "." if nivel == 1 else ".".join(partes)
        self._marca += 1
        ancla = f"_Toc{self._marca}"
        inicio = OxmlElement("w:bookmarkStart")
        inicio.set(qn("w:id"), str(self._marca))
        inicio.set(qn("w:name"), ancla)
        fin = OxmlElement("w:bookmarkEnd")
        fin.set(qn("w:id"), str(self._marca))
        ppr = p.find(qn("w:pPr"))
        ppr.addnext(inicio)
        p.append(fin)
        if nivel <= self.nivel_indice:
            self.indice.append(Entrada(numero, " ".join(texto.split()), nivel, ancla))
        return self._agregar(p)

    def texto(self, texto):
        p = copy.deepcopy(self.parrafo_modelo)
        limpiar_parrafo(p)
        poner_texto(p, texto)
        return self._agregar(p)


class Listas:
    """Listas numeradas reales, una por flujo, para que cada una reinicie en 1."""

    def __init__(self, doc):
        self.numeracion = doc.part.numbering_part.element

    def nueva(self):
        ids = [int(a.get(qn("w:abstractNumId"))) for a in self.numeracion.findall(qn("w:abstractNum"))]
        nums = [int(n.get(qn("w:numId"))) for n in self.numeracion.findall(qn("w:num"))]
        abstracto, numero = max(ids, default=0) + 1, max(nums, default=0) + 1
        a = OxmlElement("w:abstractNum")
        a.set(qn("w:abstractNumId"), str(abstracto))
        for nivel, formato, texto, izquierda in ((0, "decimal", "%1.", 1080), (1, "lowerLetter", "%2.", 1440)):
            lvl = OxmlElement("w:lvl")
            lvl.set(qn("w:ilvl"), str(nivel))
            for etiqueta, valor in (("w:start", "1"), ("w:numFmt", formato), ("w:lvlText", texto), ("w:lvlJc", "left")):
                e = OxmlElement(etiqueta)
                e.set(qn("w:val"), valor)
                lvl.append(e)
            lvl.append(_sangria(izquierda))
            a.append(lvl)
        primer_num = self.numeracion.find(qn("w:num"))
        if primer_num is None:
            self.numeracion.append(a)
        else:
            primer_num.addprevious(a)
        n = OxmlElement("w:num")
        n.set(qn("w:numId"), str(numero))
        ref = OxmlElement("w:abstractNumId")
        ref.set(qn("w:val"), str(abstracto))
        n.append(ref)
        ultimo = self.numeracion.findall(qn("w:num"))
        if ultimo:
            ultimo[-1].addnext(n)
        else:
            a.addnext(n)
        return numero


def _sangria(izquierda):
    ppr = OxmlElement("w:pPr")
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), str(izquierda))
    ind.set(qn("w:hanging"), "360")
    ppr.append(ind)
    return ppr


def numerar(parrafo, num_id, nivel, izquierda):
    """Convierte un párrafo en elemento de la lista `num_id`."""
    ppr = parrafo.find(qn("w:pPr"))
    numpr = OxmlElement("w:numPr")
    for etiqueta, valor in (("w:ilvl", nivel), ("w:numId", num_id)):
        e = OxmlElement(etiqueta)
        e.set(qn("w:val"), str(valor))
        numpr.append(e)
    for viejo in ppr.findall(qn("w:ind")):
        ppr.remove(viejo)
    ind = _sangria(izquierda)[0]
    estilo = ppr.find(qn("w:pStyle"))
    if estilo is None:
        ppr.insert(0, numpr)
    else:
        estilo.addnext(numpr)
    rpr = ppr.find(qn("w:rPr"))
    if rpr is None:
        ppr.append(ind)
    else:
        rpr.addprevious(ind)


class Indice:
    """Reconstruye el campo TOC con entradas reales."""

    def __init__(self, sdt, separador_numero, tabulador_derecho=None):
        self.contenido = sdt.find(qn("w:sdtContent"))
        parrafos = self.contenido.findall(qn("w:p"))
        codigo = "".join(i.text or "" for i in self.contenido.iter(qn("w:instrText")))
        self.codigo = codigo
        self.separador = separador_numero
        self.tabulador = tabulador_derecho
        self.modelos = {}
        for p in parrafos:
            nivel = self._nivel(texto_de(p))
            if nivel and nivel not in self.modelos:
                run = next((r for r in p.iter(qn("w:r")) if r.find(qn("w:t")) is not None), None)
                rpr = run.find(qn("w:rPr")) if run is not None else None
                self.modelos[nivel] = (copy.deepcopy(p.find(qn("w:pPr"))), copy.deepcopy(rpr))
        self.paginas = {}

    @staticmethod
    def _nivel(texto):
        m = re.match(r"\s*(\d+(?:\.\d+)*)", texto)
        return m.group(1).count(".") + 1 if m else None

    def escribir(self, entradas):
        for p in self.contenido.findall(qn("w:p")):
            self.contenido.remove(p)
        for i, e in enumerate(entradas):
            ppr, rpr = self.modelos[e.nivel]
            p = OxmlElement("w:p")
            ppr = copy.deepcopy(ppr)
            if self.tabulador:
                for tab in ppr.iter(qn("w:tab")):
                    if tab.get(qn("w:val")) == "right":
                        tab.set(qn("w:pos"), str(self.tabulador))
                        tab.set(qn("w:leader"), "dot")
            p.append(ppr)
            if i == 0:
                self._campo(p, "begin")
                instr = OxmlElement("w:instrText")
                instr.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                instr.text = self.codigo
                p.append(_run_con(instr))
                self._campo(p, "separate")
            link = OxmlElement("w:hyperlink")
            link.set(qn("w:anchor"), e.ancla)
            r = OxmlElement("w:r")
            if rpr is not None:
                r.append(copy.deepcopy(rpr))
            for hijo in self._contenido(e):
                r.append(hijo)
            link.append(r)
            p.append(link)
            if i == len(entradas) - 1:
                self._campo(p, "end")
            self.contenido.append(p)

    def _contenido(self, e):
        def t(valor):
            n = OxmlElement("w:t")
            n.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            n.text = valor
            return n

        pagina = t("0")
        self.paginas[e.ancla] = pagina
        if self.separador == "tab":
            return [t(e.numero), OxmlElement("w:tab"), t(e.titulo), OxmlElement("w:tab"), pagina]
        return [t(f"{e.numero}{self.separador}{e.titulo}"), OxmlElement("w:tab"), pagina]

    @staticmethod
    def _campo(p, tipo):
        f = OxmlElement("w:fldChar")
        f.set(qn("w:fldCharType"), tipo)
        p.append(_run_con(f))

    def poner_paginas(self, paginas):
        for ancla, numero in paginas.items():
            self.paginas[ancla].text = str(numero)


class DocumentoDocx:
    """Lo que el flujo común necesita de un documento construido."""

    def __init__(self, doc, indice, entradas):
        self.doc = doc
        self._indice = indice
        self.indice = entradas

    def guardar(self, ruta):
        self.doc.save(str(ruta))

    def poner_paginas(self, paginas):
        self._indice.poner_paginas(paginas)
