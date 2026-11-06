"""Flujo común de los tres generadores."""
import argparse
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import entrada, lint, registro, render, salida, verificar


@dataclass
class TipoDocumento:
    descripcion: str
    extension: str
    esquema_contenido: object
    validar: Callable          # datos -> [errores]
    campos: Callable           # datos -> [lint.Campo]
    reglas: list
    lint_extra: Callable       # datos -> [lint.Hallazgo]
    construir: Callable        # datos -> objeto con indice, guardar(ruta), poner_paginas(dict)
    salida_por_defecto: Callable  # datos -> Path
    textos: Callable           # ruta -> [párrafos]
    guias: list
    etiquetas_en: list
    seccion_registro: Callable  # datos -> título de su sección en el registro


def validar_entrada(tipo, datos):
    if not isinstance(datos, dict):
        raise entrada.ErrorEntrada(["El JSON debe ser un objeto"])
    errores = entrada.validar_esquema(datos, {**entrada.ESQUEMA_BASE, "contenido": tipo.esquema_contenido})
    if errores:
        raise entrada.ErrorEntrada(errores)
    errores = entrada.validar_base(datos) + tipo.validar(datos)
    if errores:
        raise entrada.ErrorEntrada(errores)


def revisar(tipo, datos):
    return lint.revisar(tipo.campos(datos), lint.REGLAS_COMUNES + tipo.reglas) + tipo.lint_extra(datos)


def bloqueos_finales(tipo, datos, hallazgos, ruta_registro):
    """Motivos que impiden una versión final. En borrador pasan a ser avisos."""
    motivos = [str(h) for h in lint.bloqueos(hallazgos)]
    motivos += [f"Pendiente en {r}: {m}" for r, m in entrada.pendientes(datos)]
    if not entrada.humanizer_declarado(datos):
        motivos.append("Falta pasar los textos por la skill humanizer y declarar redaccion.humanizer_aplicado: true")
    if not entrada.revision_confirmada(datos):
        motivos.append("Falta confirmar con el usuario la fecha, la versión, la descripción y el autor de esta edición "
                       "y declarar redaccion.revision_confirmada: true")
    motivos += registro.problemas(ruta_registro, tipo.seccion_registro(datos))
    return motivos


def construir_y_verificar(tipo, datos, destino, borrador, con_pdf):
    """Genera en un directorio temporal y mueve al destino solo si todo pasa."""
    with tempfile.TemporaryDirectory(prefix="rup-") as carpeta:
        carpeta = Path(carpeta)
        ruta = carpeta / f"documento{tipo.extension}"
        doc = tipo.construir(datos)
        doc.guardar(ruta)
        # La longitud del índice no cambia al escribir los números: basta una pasada.
        doc.poner_paginas(render.localizar(doc.indice, render.paginas_texto(render.a_pdf(ruta, carpeta))))
        doc.guardar(ruta)
        pdf = render.a_pdf(ruta, carpeta)
        paginas = len(render.paginas_texto(pdf))
        problemas = verificar.comprobar(tipo.textos(ruta), tipo.guias, tipo.etiquetas_en, borrador)
        if problemas:
            raise render.ErrorGeneracion("El documento conserva restos de la plantilla:\n  " + "\n  ".join(problemas))
        salida.mover(ruta, destino)
        if con_pdf:
            salida.mover(pdf, Path(destino).with_suffix(".pdf"))
    return paginas


def _imprimir(titulo, lineas):
    if lineas:
        print(titulo)
        for linea in lineas:
            print(f"  - {linea}")


def ejecutar(tipo, argv=None):
    p = argparse.ArgumentParser(description=tipo.descripcion)
    p.add_argument("entrada", help="archivo JSON con el contenido")
    p.add_argument("--salida", help="ruta del documento (por defecto, en docs/)")
    p.add_argument("--borrador", action="store_true", help="admite pendientes y hallazgos; no es versión final")
    p.add_argument("--sobrescribir", action="store_true", help="reemplaza el archivo de salida si existe")
    p.add_argument("--pdf", action="store_true", help="deja también una copia en PDF")
    p.add_argument("--registro", help="registro de preguntas y respuestas (por defecto, junto al JSON)")
    p.add_argument("--solo-lint", action="store_true", help="revisa el JSON sin crear ningún documento")
    a = p.parse_args(argv)
    try:
        datos = entrada.cargar(a.entrada)
        validar_entrada(tipo, datos)
        hallazgos = revisar(tipo, datos)
        ruta_registro = a.registro or registro.ruta_por_defecto(a.entrada)
        motivos = bloqueos_finales(tipo, datos, hallazgos, ruta_registro)
        _imprimir("Avisos:", [str(h) for h in lint.avisos(hallazgos)])
        if a.solo_lint:
            r = datos["historial"][-1]
            print(f"Edición: versión {r['version']}, {r['fecha']}, {r['autor']}. {r['descripcion']}")
            _imprimir("Bloquean la versión final:", motivos)
            print(f"Lint: {len(motivos)} bloqueos, {len(lint.avisos(hallazgos))} avisos")
            return 1 if motivos else 0
        if motivos and not a.borrador:
            _imprimir("No se generó el documento:", motivos)
            return 1
        destino = Path(a.salida) if a.salida else tipo.salida_por_defecto(datos)
        render.requerir_herramientas()
        salida.comprobar_destino(destino, a.sobrescribir)
        paginas = construir_y_verificar(tipo, datos, destino, a.borrador, a.pdf)
    except entrada.ErrorEntrada as e:
        _imprimir("Errores en el JSON:", e.errores)
        return 1
    except render.ErrorGeneracion as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    if a.borrador:
        _imprimir("BORRADOR, no es versión final:", motivos)
    print(f"Generado: {destino} ({paginas} páginas)")
    return 0
