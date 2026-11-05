#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-docx", "lxml"]
# ///
"""Genera la Especificación Suplementaria sobre la plantilla RUP."""
import copy
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_rup-comun"))

import docx  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

from rup_comun import cli, docx_util as du, entrada, verificar  # noqa: E402
from rup_comun.entrada import Opcional  # noqa: E402
from rup_comun.lint import AVISA, BLOQUEA, Campo, Hallazgo, Regla  # noqa: E402
from rup_comun.render import ErrorGeneracion  # noqa: E402

PLANTILLA = Path(__file__).resolve().parents[1] / "assets" / "plantilla.docx"
TITULO = "Especificación Suplementaria"
NO_APLICA = "No aplica."

# Textos que identifican cada pieza de la plantilla. Una prueba falla si alguno desaparece.
T_PROYECTO = "<Nombre del proyecto>"
T_VERSION = "Versión <1.0>"
T_HISTORIAL = "Historial de revisiones"
T_INDICE = "Tabla de contenido"
T_TITULO_CUERPO = "Especificación complementaria"
T_H1 = "Introducción"
T_H2 = "Objetivo"
T_CUERPO = "La descripción del requisito."
INICIO_GUIA_PORTADA = ("[Nota:", "Para personalizar los campos")
PIEZAS = (T_PROYECTO, T_VERSION, T_HISTORIAL, T_INDICE, T_TITULO_CUERPO, T_H1, T_H2, T_CUERPO)

REQUISITO = {"titulo": str, "descripcion": str, "casos_uso": Opcional([str])}
CON_REQUISITOS = {"requisitos": Opcional([REQUISITO]), "no_aplica": Opcional(bool)}
CON_TEXTO = {"texto": Opcional([str]), "no_aplica": Opcional(bool)}

# Clave del JSON, título y forma. El orden es el de la plantilla.
SECCIONES = [
    ("funcionalidad", "Funcionalidad", "requisitos"),
    ("usabilidad", "Usabilidad", "requisitos"),
    ("confiabilidad", "Confiabilidad", "requisitos"),
    ("desempeno", "Desempeño", "requisitos"),
    ("soporte", "Soporte", "requisitos"),
    ("restricciones_diseno", "Restricciones de diseño", "requisitos"),
    ("documentacion", "Requisitos del sistema de documentación y ayuda para el usuario en línea", "texto"),
    ("componentes_adquiridos", "Componentes adquiridos", "texto"),
    ("interfaces", "Interfaces", "interfaces"),
    ("licencia", "Requisitos de licencia", "texto"),
    ("avisos_legales", "Avisos legales, de derechos de autor y otros avisos", "texto"),
    ("normas", "Normas aplicables", "texto"),
]
INTERFACES = [
    ("usuario", "Interfaces de usuario"),
    ("hardware", "Interfaces de hardware"),
    ("software", "Interfaces de software"),
    ("comunicacion", "Interfaces de comunicación"),
]
MEDIBLES = ("usabilidad", "confiabilidad", "desempeno")

ESQUEMA = {
    "introduccion": {
        "objetivo": str,
        "alcance": str,
        "definiciones": {"remite_glosario": Opcional(bool), "texto": Opcional(str)},
        "referencias": [str],
        "descripcion_general": str,
    },
    **{clave: CON_REQUISITOS if forma == "requisitos" else CON_TEXTO
       for clave, _, forma in SECCIONES if forma != "interfaces"},
    "interfaces": {clave: CON_TEXTO for clave, _ in INTERFACES},
}

REQ = ("requisito",)
REGLAS = [
    Regla("S-SUPERLATIVO", r"\b(?:el|la|los|las)\s+(?:mejor|mejores|peor|peores)\b|\bóptim[oa]s?\b"
                           r"|\bmáxima calidad\b|\bmayor posible\b", AVISA,
          "Superlativo: indica el valor o criterio exacto.", REQ),
    Regla("S-COMPARATIVO", r"\bmás\s+(?!de\b)\w+|\bmenos\s+(?!de\b)\w+|\b(?:mejor|peor)(?:es)? que\b", AVISA,
          "Comparativo sin referencia: indica contra qué se compara.", REQ),
    Regla("S-NEGATIVO", r"\bno deberán?\b", AVISA, "Sentencia negativa: di qué hace el Sistema.", REQ),
    Regla("S7", r"\bcrític[oa]s?\b|\badecuad[oa]s?\b|\bsegur[oa]s?\b", AVISA,
          "Término que hay que definir: aclara qué significa aquí.", REQ),
]
VAGOS = re.compile(r"\b(?:rápid[oa]s?|rápidamente|lent[oa]s?|fácil(?:es)?|alta disponibilidad|alto rendimiento"
                   r"|tiempo razonable|buen rendimiento|disponible siempre)\b", re.IGNORECASE)
PATRON_EARS = re.compile(r"^(?:El Sistema|Cuando\b|Mientras\b|Si\b|Donde\b)")


def _forma(valor, ruta, clave_contenido):
    """Una sección trae contenido o declara no_aplica. Nunca ambas cosas."""
    con_contenido = bool(valor.get(clave_contenido))
    no_aplica = valor.get("no_aplica") is True
    if con_contenido and no_aplica:
        return [f"{ruta}: declara contenido y no_aplica; deja uno solo"]
    if not con_contenido and not no_aplica:
        return [f"{ruta}: sin contenido; agrega {clave_contenido} o declara no_aplica: true"]
    return []


def validar(datos):
    c = datos["contenido"]
    errores = []
    d = c["introduccion"]["definiciones"]
    if (d.get("remite_glosario") is True) == ("texto" in d):
        errores.append("contenido.introduccion.definiciones: indica remite_glosario: true o texto, solo uno")
    for clave, _, forma in SECCIONES:
        if forma == "interfaces":
            for sub, _ in INTERFACES:
                errores += _forma(c["interfaces"][sub], f"contenido.interfaces.{sub}", "texto")
        else:
            errores += _forma(c[clave], f"contenido.{clave}", forma)
    return errores


def _requisitos(c):
    for clave, _, forma in SECCIONES:
        if forma == "requisitos":
            for i, r in enumerate(c[clave].get("requisitos", [])):
                yield clave, f"contenido.{clave}.requisitos[{i}].descripcion", r


def campos(datos):
    c = datos["contenido"]
    i = c["introduccion"]
    lista = [Campo(f"contenido.introduccion.{k}", i[k]) for k in ("objetivo", "alcance", "descripcion_general")]
    if "texto" in i["definiciones"]:
        lista.append(Campo("contenido.introduccion.definiciones.texto", i["definiciones"]["texto"]))
    lista += [Campo(ruta, r["descripcion"], "requisito") for _, ruta, r in _requisitos(c)]
    for clave, _, forma in SECCIONES:
        if forma == "texto":
            lista += [Campo(f"contenido.{clave}.texto[{n}]", t) for n, t in enumerate(c[clave].get("texto", []))]
    for sub, _ in INTERFACES:
        lista += [Campo(f"contenido.interfaces.{sub}.texto[{n}]", t)
                  for n, t in enumerate(c["interfaces"][sub].get("texto", []))]
    return lista


def lint_extra(datos):
    hallazgos = []
    for seccion, ruta, r in _requisitos(datos["contenido"]):
        texto = r["descripcion"].strip()
        pendiente = entrada.PENDIENTE.search(texto)
        if not re.search(r"\bdeberán?\b", texto) and not entrada.PENDIENTE.fullmatch(texto):
            hallazgos.append(Hallazgo(ruta, texto[:50], "S3", "El requisito debe contener «deberá».", BLOQUEA))
        if not PATRON_EARS.match(texto) and not pendiente:
            hallazgos.append(Hallazgo(ruta, texto[:50], "S4",
                                      "Usa un patrón: El Sistema deberá, Cuando, Mientras, Si ... entonces, Donde.", AVISA))
        if texto.startswith("Si ") and "entonces" not in texto:
            hallazgos.append(Hallazgo(ruta, texto[:50], "S4", "El patrón «Si» lleva «entonces».", AVISA))
        if seccion in MEDIBLES and not pendiente and not re.search(r"\d", texto):
            m = VAGOS.search(texto)
            if m:
                hallazgos.append(Hallazgo(ruta, m.group(0), "S-MEDIBLE", "Término vago sin cifra ni criterio.", AVISA))
    return hallazgos


def buscar(hijos, texto):
    for el in hijos:
        if du.texto_de(el).strip() == texto:
            return el
    raise ErrorGeneracion(f"La plantilla no contiene la pieza «{texto}»")


def _modelo_cuerpo(parrafo):
    """El cuerpo de esta plantilla solo existe como guía azul: se le quita ese formato."""
    p = copy.deepcopy(parrafo)
    for rpr in p.iter(qn("w:rPr")):
        for etiqueta in ("w:i", "w:iCs"):
            for e in rpr.findall(qn(etiqueta)):
                e.set(qn("w:val"), "0")
        for e in rpr.findall(qn("w:color")):
            e.set(qn("w:val"), "000000")
    return p


def _requisitos_o_nada(cuerpo, valor):
    if valor.get("no_aplica"):
        cuerpo.texto(NO_APLICA)
    for r in valor.get("requisitos", []):
        cuerpo.titulo(2, r["titulo"])
        cuerpo.texto(r["descripcion"])
        if r.get("casos_uso"):
            cuerpo.texto("Casos de uso relacionados: " + ", ".join(r["casos_uso"]) + ".")


def _texto_o_nada(cuerpo, valor):
    if valor.get("no_aplica"):
        cuerpo.texto(NO_APLICA)
    for t in valor.get("texto", []):
        cuerpo.texto(t)


def construir(datos):
    c, proyecto, documento = datos["contenido"], datos["proyecto"], datos["documento"]
    doc = docx.Document(str(PLANTILLA))
    body = doc.element.body
    hijos = list(body)

    # Portada
    du.poner_texto(buscar(hijos, T_PROYECTO), proyecto["nombre"])
    du.poner_texto(buscar(hijos, T_VERSION), f"Versión {documento['version']}")
    for el in hijos:
        if el.tag == qn("w:p") and du.texto_de(el).startswith(INICIO_GUIA_PORTADA):
            body.remove(el)

    # Historial e índice
    du.llenar_tabla(body.find(qn("w:tbl")), [[r["fecha"], r["version"], r["descripcion"], r["autor"]]
                                             for r in datos["historial"]])
    # El tabulador de la plantilla queda fuera de la página y oculta los números.
    indice = du.Indice(body.find(qn("w:sdt")), " ", tabulador_derecho=9350)

    # Encabezados y pies
    for parte, es_encabezado in du.partes_encabezado_pie(doc):
        du.aplanar_campos(parte, {"DOCPROPERTY": proyecto["empresa"] if es_encabezado else proyecto["organizacion"]})
        du.reemplazar(parte, {
            "<Nombre del proyecto>": proyecto["nombre"],
            "Versión: <1.0>": f"Versión: {documento['version']}",
            "Especificación complementaria": TITULO,
            "Fecha: <dd/mmm/aa>": f"Fecha: {documento['fecha']}",
            "<identificador del documento>": proyecto["identificador"],
            ", 2001": f", {entrada.anio(datos)}",
            "Página": "Página ",
        })

    # Cuerpo
    titulo_cuerpo = buscar(hijos, T_TITULO_CUERPO)
    du.poner_texto(titulo_cuerpo, TITULO)
    cuerpo = du.Cuerpo(
        doc, hijos[hijos.index(titulo_cuerpo) + 1],
        {1: buscar(hijos, T_H1), 2: buscar(hijos, T_H2)},
        _modelo_cuerpo(buscar(hijos, T_CUERPO)), nivel_indice=2,
    )
    intro = c["introduccion"]
    cuerpo.titulo(1, "Introducción")
    cuerpo.titulo(2, "Objetivo")
    cuerpo.texto(intro["objetivo"])
    cuerpo.titulo(2, "Alcance")
    cuerpo.texto(intro["alcance"])
    cuerpo.titulo(2, "Definiciones, acrónimos y abreviaturas")
    cuerpo.texto(intro["definiciones"].get("texto", "Las definiciones se encuentran en el Glosario del proyecto."))
    cuerpo.titulo(2, "Referencias")
    for r in intro["referencias"] or ["Este documento no cita referencias."]:
        cuerpo.texto(r)
    cuerpo.titulo(2, "Descripción general")
    cuerpo.texto(intro["descripcion_general"])
    for clave, titulo, forma in SECCIONES:
        cuerpo.titulo(1, titulo)
        if forma == "requisitos":
            _requisitos_o_nada(cuerpo, c[clave])
        elif forma == "texto":
            _texto_o_nada(cuerpo, c[clave])
        else:
            for sub, subtitulo in INTERFACES:
                cuerpo.titulo(2, subtitulo)
                _texto_o_nada(cuerpo, c["interfaces"][sub])

    indice.escribir(cuerpo.indice)
    du.poner_idioma(doc)
    du.propiedades(doc, TITULO, datos)
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
    salida_por_defecto=lambda d: Path("docs") / "Especificacion Suplementaria.docx",
    textos=verificar.textos_docx,
    guias=verificar.guias_de(verificar.textos_docx(PLANTILLA)) + [
        "Para personalizar los campos", "La descripción del requisito", "Cuando se emplean herramientas",
        "Requisitos legales y reglamentarios", "Especificar el tiempo de capacitación",
    ],
    etiquetas_en=[r"(?i)Especificación complementaria", r", 2001\b", r"Página\d"],
)

if __name__ == "__main__":
    sys.exit(cli.ejecutar(TIPO))
