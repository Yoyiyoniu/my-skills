#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-docx", "lxml"]
# ///
"""Genera una Especificación de Caso de Uso sobre la plantilla RUP."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_rup-comun"))

import docx  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

from rup_comun import cli, docx_util as du, entrada, lint, verificar  # noqa: E402
from rup_comun.entrada import Opcional  # noqa: E402
from rup_comun.lint import AVISA, BLOQUEA, Campo, Hallazgo, Regla  # noqa: E402
from rup_comun.render import ErrorGeneracion  # noqa: E402

PLANTILLA = Path(__file__).resolve().parents[1] / "assets" / "plantilla.docx"
FIN = "El caso de uso finaliza."

# Textos que identifican cada pieza de la plantilla. Una prueba falla si alguno desaparece.
T_PORTADA_TITULO = "Caso uso < name>"
T_PORTADA_VERSION = "Version <1.0>"
T_HISTORIAL = "Revision History"
T_INDICE = "Table of Contents"
T_TITULO_CUERPO = "Caso uso importacion"
T_H1 = "Flow of Events"
T_H2 = "Brief Description"
T_H3 = "< First Alternative Flow >"
T_H4 = "< An Alternative Subflow >"
ESTILO_CUERPO = "BodyText"
ESTILO_GUIA = "InfoBlue"
PIEZAS = (T_PORTADA_TITULO, T_PORTADA_VERSION, T_HISTORIAL, T_INDICE, T_TITULO_CUERPO, T_H1, T_H2, T_H3, T_H4)

CONDICION = {"nombre": str, "descripcion": str}
PASO = {"paso": str, "subpasos": Opcional([str])}
SUBFLUJO = {
    "nombre": str, "desde_paso": int, "condicion": str, "pasos": [PASO],
    "regresa_a_paso": Opcional(int), "finaliza": Opcional(bool),
}
ESQUEMA = {
    "nombre": str,
    "actores": [str],
    "actor_principal": str,
    "descripcion": str,
    "inicio": str,
    "flujo_basico": [PASO],
    "flujos_alternos": [{**SUBFLUJO, "subflujos": Opcional([SUBFLUJO])}],
    "requerimientos_especiales": [CONDICION],
    "precondiciones": [CONDICION],
    "postcondiciones": [CONDICION],
    "puntos_extension": [{"nombre": str, "paso": int, "descripcion": str}],
}

PASOS = ("paso_basico", "paso_alterno")
REGLAS = [
    Regla("U15", r"^(?:si|en caso de|cuando|mientras|siempre que)\b|,\s*si\b", BLOQUEA,
          "Condición en el flujo básico: muévela a un flujo alterno.", ("paso_basico",)),
    Regla("U3-OPCIONAL", r"\b(?:puede|pueden|podrá|podrán|debería|deberían|opcionalmente|quizá|quizás|posiblemente)\b",
          BLOQUEA, "Acción opcional: escribe un flujo alterno con la condición que la activa.", PASOS),
    Regla("U6", r"\bclics?\b|\bbotón\b|\bbotones\b|\bpantallas?\b|\bmenús?\b|\bpestañas?\b", BLOQUEA,
          "Detalle de interfaz: expresa la intención del actor.", PASOS),
    Regla("U8", r"\bbases? de datos\b|\bAPIs?\b|\bSQL\b|\bendpoints?\b|\bservidor(?:es)?\b", BLOQUEA,
          "Detalle de implementación: describe lo que el Sistema hace para el actor.", PASOS),
    Regla("U8-TABLA", r"\btablas?\b|\bcódigo\b", AVISA,
          "Posible detalle de implementación: confirma que es un término del dominio.", PASOS),
    Regla("ADVERBIO", r"\b(?:correctamente|exitosamente|satisfactoriamente|automáticamente)\b", BLOQUEA,
          "Adverbio de relleno: elimínalo.", PASOS),
    Regla("ADVERBIO-MENTE", r"\b(?!correctamente\b|exitosamente\b|satisfactoriamente\b|automáticamente\b)\w{3,}mente\b",
          AVISA, "Adverbio: confirma que aporta un hecho.", PASOS),
    Regla("U3-PASIVA", r"\b(?:es|son|fue|fueron|será|serán)\s+\w+(?:ad|id)[oa]s?\b", AVISA,
          "Voz pasiva: escribe la acción en activa.", PASOS),
    Regla("U5", r"\bverifica(?:r)?\s+(?:si|que)\b|\bcomprueba\s+(?:si|que)\b", AVISA,
          "Escribe «El Sistema valida <dato o regla>». El fallo va en un flujo alterno.", PASOS),
    Regla("PRONOMBRE", r"\b(?:él|ella|ellos|ellas)\b", AVISA,
          "Pronombre: usa el nombre completo del actor.", PASOS),
    Regla("U16", r"\bno\b", AVISA, "Negación en el flujo básico: resérvala para flujos alternos.", ("paso_basico",)),
    Regla("U7", r"\b(?:ingresa|introduce|captura|proporciona)\s+(?:sus datos|los datos|la información)\s*\.?$", AVISA,
          "Dato genérico: nombra los datos que se intercambian.", PASOS),
    Regla("U-CODIGO", r"\bIF\b|\bTHEN\b|\bELSE\b|\bWHILE\b", AVISA, "Forma de código: usa lenguaje natural.", PASOS),
]


def pasos_basicos(c):
    """Flujo básico con su cierre: el último paso siempre indica cómo termina."""
    pasos = list(c["flujo_basico"])
    if pasos and pasos[-1]["paso"].strip() != FIN:
        pasos.append({"paso": FIN})
    return pasos


def todos_los_flujos(c):
    """Produce (ruta, flujo) para flujos alternos y subflujos."""
    for i, f in enumerate(c["flujos_alternos"]):
        ruta = f"contenido.flujos_alternos[{i}]"
        yield ruta, f
        for j, s in enumerate(f.get("subflujos", [])):
            yield f"{ruta}.subflujos[{j}]", s


def validar(datos):
    c = datos["contenido"]
    errores = []
    if not c["actores"]:
        errores.append("contenido.actores: debe tener al menos un actor")
    if c["actor_principal"] not in c["actores"]:
        errores.append(f"contenido.actor_principal: «{c['actor_principal']}» no está en contenido.actores")
    if c["actor_principal"] not in c["inicio"] and not entrada.PENDIENTE.search(c["inicio"]):
        errores.append(f"contenido.inicio: debe nombrar al actor que inicia («{c['actor_principal']}»)")
    if not c["flujo_basico"]:
        errores.append("contenido.flujo_basico: debe tener al menos un paso")
    total = len(pasos_basicos(c))

    def paso_valido(ruta, nombre, paso):
        if not 1 <= paso <= total:
            errores.append(f"{ruta}: «{nombre}» cita el paso {paso} y el flujo básico tiene {total} pasos")

    for ruta, f in todos_los_flujos(c):
        paso_valido(f"{ruta}.desde_paso", f["nombre"], f["desde_paso"])
        if not f["pasos"]:
            errores.append(f"{ruta}.pasos: «{f['nombre']}» debe tener al menos un paso")
        regresa, finaliza = "regresa_a_paso" in f, f.get("finaliza") is True
        if regresa and finaliza:
            errores.append(f"{ruta}: «{f['nombre']}» declara dos desenlaces; deja uno solo")
        elif not regresa and not finaliza:
            errores.append(f"{ruta}: «{f['nombre']}» no indica cómo termina (regresa_a_paso o finaliza)")
        elif regresa:
            paso_valido(f"{ruta}.regresa_a_paso", f["nombre"], f["regresa_a_paso"])
    for i, p in enumerate(c["puntos_extension"]):
        paso_valido(f"contenido.puntos_extension[{i}].paso", p["nombre"], p["paso"])
    return errores


def _campos_pasos(ruta, pasos, clase):
    for i, p in enumerate(pasos):
        yield Campo(f"{ruta}[{i}]", p["paso"], clase)
        for j, s in enumerate(p.get("subpasos", [])):
            yield Campo(f"{ruta}[{i}].subpasos[{j}]", s)


def campos(datos):
    c = datos["contenido"]
    lista = [Campo("contenido.descripcion", c["descripcion"]), Campo("contenido.inicio", c["inicio"])]
    lista += _campos_pasos("contenido.flujo_basico", c["flujo_basico"], "paso_basico")
    for ruta, f in todos_los_flujos(c):
        lista.append(Campo(f"{ruta}.condicion", f["condicion"]))
        lista += _campos_pasos(f"{ruta}.pasos", f["pasos"], "paso_alterno")
    for seccion in ("requerimientos_especiales", "precondiciones", "postcondiciones", "puntos_extension"):
        for i, item in enumerate(c[seccion]):
            lista.append(Campo(f"contenido.{seccion}[{i}].descripcion", item["descripcion"]))
    return lista


def lint_extra(datos):
    c = datos["contenido"]
    actores = "|".join(re.escape(a) for a in sorted({*c["actores"], "Sistema"}, key=len, reverse=True))
    sujeto = re.compile(rf"^(?:(?:El|La|Los|Las)\s+)?(?:{actores})\b")
    hallazgos = []
    for campo in campos(datos):
        texto = campo.texto.strip()
        if campo.clase in PASOS and texto != FIN and not sujeto.match(texto) and not entrada.PENDIENTE.match(texto):
            hallazgos.append(Hallazgo(campo.ruta, texto[:50], "U9",
                                      "El paso debe empezar por un actor registrado o «El Sistema».", BLOQUEA))
    if len(pasos_basicos(c)) > 9:
        hallazgos.append(Hallazgo("contenido.flujo_basico", f"{len(pasos_basicos(c))} pasos", "U10",
                                  "Más de nueve pasos: divide el flujo en subflujos.", AVISA))
    if not re.match(r"^\w+(?:ar|er|ir)\b", c["nombre"]):
        hallazgos.append(Hallazgo("contenido.nombre", c["nombre"], "U1",
                                  "El nombre se escribe con verbo en infinitivo y objeto.", AVISA))
    return hallazgos


def buscar(hijos, texto):
    for el in hijos:
        if du.texto_de(el).strip() == texto:
            return el
    raise ErrorGeneracion(f"La plantilla no contiene la pieza «{texto}»")


def _escribir_pasos(cuerpo, listas, pasos):
    num = listas.nueva()
    for p in pasos:
        du.numerar(cuerpo.texto(p["paso"]), num, 0, 1080)
        for s in p.get("subpasos", []):
            du.numerar(cuerpo.texto(s), num, 1, 1440)


def _escribir_flujo(cuerpo, listas, f, nivel):
    cuerpo.titulo(nivel, f["nombre"])
    cuerpo.texto(f"Este flujo comienza en el paso {f['desde_paso']} del flujo básico cuando {f['condicion'].rstrip('.')}.")
    _escribir_pasos(cuerpo, listas, f["pasos"])
    cuerpo.texto(f"El flujo regresa al paso {f['regresa_a_paso']}." if "regresa_a_paso" in f else FIN)


def _seccion(cuerpo, titulo, items, vacio):
    cuerpo.titulo(1, titulo)
    if not items:
        cuerpo.texto(vacio)
    for item in items:
        cuerpo.titulo(2, item["nombre"])
        cuerpo.texto(item["descripcion"])


def construir(datos):
    c, proyecto, documento = datos["contenido"], datos["proyecto"], datos["documento"]
    titulo = f"Caso de uso: {c['nombre']}"
    doc = docx.Document(str(PLANTILLA))
    body = doc.element.body
    hijos = list(body)

    # Portada
    du.aplanar_campos(hijos[0], {"SUBJECT": proyecto["nombre"]})
    du.poner_texto(buscar(hijos, T_PORTADA_TITULO), titulo)
    du.poner_texto(buscar(hijos, T_PORTADA_VERSION), f"Versión {documento['version']}")

    # Guía de la portada y del principio del cuerpo
    titulo_cuerpo = buscar(hijos, T_TITULO_CUERPO)
    for el in hijos[:hijos.index(titulo_cuerpo)]:
        estilo = el.find(f"{qn('w:pPr')}/{qn('w:pStyle')}") if el.tag == qn("w:p") else None
        if estilo is not None and estilo.get(qn("w:val")) == ESTILO_GUIA:
            body.remove(el)

    # Historial e índice
    du.poner_texto(buscar(hijos, T_HISTORIAL), "Historial de revisiones")
    du.poner_texto(buscar(hijos, T_INDICE), "Índice")
    tabla = body.find(qn("w:tbl"))
    du.traducir_exacto(tabla, {"Date": "Fecha", "Version": "Versión", "Description": "Descripción", "Author": "Autor"})
    du.llenar_tabla(tabla, [[r["fecha"], r["version"], r["descripcion"], r["autor"]] for r in datos["historial"]])
    indice = du.Indice(body.find(qn("w:sdt")), "tab")

    # Encabezados y pies
    for parte, es_encabezado in du.partes_encabezado_pie(doc):
        du.aplanar_campos(parte, {
            "SUBJECT": proyecto["nombre"],
            "TITLE": titulo,
            "DOCPROPERTY": proyecto["empresa"] if es_encabezado else proyecto["organizacion"],
            "DATE": entrada.anio(datos),
        })
        du.reemplazar(parte, {
            "Version:           <1.0>": f"Versión: {documento['version']}",
            "Date:  <dd/mmm/yy>": f"Fecha: {documento['fecha']}",
            "<document identifier>": proyecto["identificador"],
            "Confidential": "Confidencial",
            "Page ": "Página ",
        })

    # Cuerpo
    du.poner_texto(titulo_cuerpo, titulo)
    cuerpo_modelo = next(p for p in hijos if p.tag == qn("w:p")
                         and p.find(f"{qn('w:pPr')}/{qn('w:pStyle')}") is not None
                         and p.find(f"{qn('w:pPr')}/{qn('w:pStyle')}").get(qn("w:val")) == ESTILO_CUERPO
                         and p.find(f"{qn('w:pPr')}/{qn('w:sectPr')}") is None)
    cuerpo = du.Cuerpo(
        doc, hijos[hijos.index(titulo_cuerpo) + 1],
        {1: buscar(hijos, T_H1), 2: buscar(hijos, T_H2), 3: buscar(hijos, T_H3), 4: buscar(hijos, T_H4)},
        cuerpo_modelo, nivel_indice=3,
    )
    listas = du.Listas(doc)
    cuerpo.titulo(1, c["nombre"])
    cuerpo.titulo(2, "Breve descripción")
    cuerpo.texto(c["descripcion"])
    cuerpo.titulo(1, "Flujo de eventos")
    cuerpo.titulo(2, "Flujo básico")
    cuerpo.texto(f"Este caso de uso comienza cuando {c['inicio'].rstrip('.')}.")
    _escribir_pasos(cuerpo, listas, pasos_basicos(c))
    cuerpo.titulo(2, "Flujos alternos")
    if not c["flujos_alternos"]:
        cuerpo.texto("No se identificaron flujos alternos para este caso de uso.")
    for f in c["flujos_alternos"]:
        _escribir_flujo(cuerpo, listas, f, 3)
        for s in f.get("subflujos", []):
            _escribir_flujo(cuerpo, listas, s, 4)
    _seccion(cuerpo, "Requerimientos especiales", c["requerimientos_especiales"],
             "No se identificaron requerimientos especiales para este caso de uso.")
    _seccion(cuerpo, "Precondiciones", c["precondiciones"],
             "No se identificaron precondiciones para este caso de uso.")
    _seccion(cuerpo, "Postcondiciones", c["postcondiciones"],
             "No se identificaron postcondiciones para este caso de uso.")
    _seccion(cuerpo, "Puntos de extensión",
             [{"nombre": p["nombre"], "descripcion": f"Paso {p['paso']} del flujo básico. {p['descripcion']}"}
              for p in c["puntos_extension"]],
             "No se identificaron puntos de extensión para este caso de uso.")

    indice.escribir(cuerpo.indice)
    du.normalizar_alineacion(doc)
    du.poner_idioma(doc)
    du.propiedades(doc, titulo, datos)
    return du.DocumentoDocx(doc, indice, cuerpo.indice)


TIPO = cli.TipoDocumento(
    descripcion=__doc__,
    extension=".docx",
    esquema_contenido=ESQUEMA,
    validar=validar,
    campos=campos,
    reglas=REGLAS,
    lint_extra=lint_extra,
    construir=construir,
    salida_por_defecto=lambda d: Path("docs") / f"UCS {d['contenido']['nombre']}.docx",
    textos=verificar.textos_docx,
    guias=verificar.guias_de(verificar.textos_docx(PLANTILLA)) + [
        "The use-case diagrams", "The use case describes", "Simple alternatives may", "A picture is sometimes",
    ],
    seccion_registro=lambda d: f"UCS {d['contenido']['nombre']}",
    etiquetas_en=[
        r"\bRevision History\b", r"\bTable of Contents\b", r"\bUse-Case\b", r"\bUse Case\b", r"\bFlow of Events\b",
        r"\bBasic Flow\b", r"\bAlternative Flows?\b", r"\bSpecial Requirements?\b", r"\bPreconditions?\b",
        r"\bPostconditions?\b", r"\bExtension Points?\b", r"\bConfidential\b", r"\bDate\b", r"\bVersion\b",
        r"\bPage\b", r"\bDescription\b", r"\bAuthor\b", r"Caso uso",
    ],
)

if __name__ == "__main__":
    sys.exit(cli.ejecutar(TIPO))
