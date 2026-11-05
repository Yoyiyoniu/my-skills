"""Las piezas que usan los generadores siguen en las plantillas, y las originales no cambiaron."""
import zipfile

import docx
from conftest import SKILLS, escribir, limpiar_pendientes
from docx.oxml.ns import qn
from lxml import etree

from rup_comun import cli, docx_util as du


def textos_cuerpo(ruta):
    return {du.texto_de(el).strip() for el in docx.Document(str(ruta)).element.body}


def test_piezas_caso_de_uso(uc):
    textos = textos_cuerpo(uc.PLANTILLA)
    assert all(p.strip() in textos for p in uc.PIEZAS)


def test_piezas_suplementaria(supl):
    textos = textos_cuerpo(supl.PLANTILLA)
    assert all(p in textos for p in supl.PIEZAS)


def test_piezas_glosario(glos):
    raiz = etree.fromstring(zipfile.ZipFile(glos.PLANTILLA).read("content.xml"))
    textos = {"".join(el.itertext()).strip() for el in raiz.find(".//office:text", glos.NS)}
    assert all(p in textos for p in glos.PIEZAS)


def test_generar_no_modifica_plantillas(uc, datos_uc, tmp_path):
    antes = uc.PLANTILLA.read_bytes()
    cli.ejecutar(uc.TIPO, [escribir(tmp_path, limpiar_pendientes(datos_uc)), "--salida", str(tmp_path / "o.docx")])
    assert uc.PLANTILLA.read_bytes() == antes


def test_originales_presentes():
    for ruta in ("rup-caso-de-uso/assets/original/Plantilla Caso de Uso.doc",
                 "rup-especificacion-suplementaria/assets/original/Plantilla Especificaciones Suplementarias.docx",
                 "rup-glosario/assets/original/rup_gloss.odt"):
        assert (SKILLS / ruta).exists()


def test_formato_conservado(uc, datos_uc, tmp_path):
    destino = tmp_path / "o.docx"
    assert cli.ejecutar(uc.TIPO, [escribir(tmp_path, limpiar_pendientes(datos_uc)), "--salida", str(destino)]) == 0
    a, b = docx.Document(str(uc.PLANTILLA)), docx.Document(str(destino))
    assert (a.sections[-1].page_width, a.sections[-1].left_margin) == (b.sections[-1].page_width, b.sections[-1].left_margin)
    estilos = {e.get(qn("w:val")) for e in b.element.body.iter(qn("w:pStyle"))}
    assert {"Heading1", "Heading2", "Heading3", "BodyText"} <= estilos
    assert "InfoBlue" not in estilos
