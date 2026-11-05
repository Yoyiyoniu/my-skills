"""Reglas comunes: entrada, lint, render, escritura y verificación."""
import pytest
from conftest import escribir, limpiar_pendientes

from rup_comun import cli, entrada, lint, render, salida, verificar
from rup_comun.lint import AVISA, BLOQUEA, Campo


def errores_de(tipo, datos):
    with pytest.raises(entrada.ErrorEntrada) as e:
        cli.validar_entrada(tipo, datos)
    return e.value.errores


def test_falta_campo_obligatorio(uc, datos_uc):
    del datos_uc["documento"]["version"]
    assert any("documento.version" in e for e in errores_de(uc.TIPO, datos_uc))


def test_tipo_incorrecto(uc, datos_uc):
    datos_uc["contenido"]["flujos_alternos"][0]["desde_paso"] = "cuatro"
    assert any("desde_paso" in e and "número" in e for e in errores_de(uc.TIPO, datos_uc))


def test_json_invalido(tmp_path):
    ruta = tmp_path / "x.json"
    ruta.write_text("{", encoding="utf-8")
    with pytest.raises(entrada.ErrorEntrada):
        entrada.cargar(ruta)


def test_falta_campo_no_escribe_archivo(uc, datos_uc, tmp_path):
    del datos_uc["documento"]["version"]
    salida_doc = tmp_path / "out.docx"
    assert cli.ejecutar(uc.TIPO, [escribir(tmp_path, datos_uc), "--salida", str(salida_doc)]) == 1
    assert not salida_doc.exists()


def test_version_incoherente(uc, datos_uc):
    datos_uc["documento"]["version"] = "1.2"
    errores = errores_de(uc.TIPO, datos_uc)
    assert any("1.2" in e and "1.0" in e for e in errores)


def test_historial_vacio(uc, datos_uc):
    datos_uc["historial"] = []
    assert any("historial" in e for e in errores_de(uc.TIPO, datos_uc))


def test_fecha_con_formato_invalido(uc, datos_uc):
    datos_uc["documento"]["fecha"] = "2026-11-05"
    assert any("documento.fecha" in e for e in errores_de(uc.TIPO, datos_uc))


def test_pendientes_bloquean_final_y_se_listan(uc, datos_uc, tmp_path, capsys):
    salida_doc = tmp_path / "out.docx"
    assert cli.ejecutar(uc.TIPO, [escribir(tmp_path, datos_uc), "--salida", str(salida_doc)]) == 1
    salida_impresa = capsys.readouterr().out
    assert "nombre oficial del proyecto" in salida_impresa and "autor" in salida_impresa
    assert not salida_doc.exists()


def test_borrador_conserva_pendientes(uc, datos_uc, tmp_path):
    salida_doc = tmp_path / "out.docx"
    assert cli.ejecutar(uc.TIPO, [escribir(tmp_path, datos_uc), "--borrador", "--salida", str(salida_doc)]) == 0
    assert any("[PENDIENTE" in t for t in verificar.textos_docx(salida_doc))


def test_humanizer_sin_declarar_bloquea(uc, datos_uc, tmp_path, capsys):
    d = limpiar_pendientes(datos_uc)
    d["redaccion"]["humanizer_aplicado"] = False
    assert cli.ejecutar(uc.TIPO, [escribir(tmp_path, d), "--salida", str(tmp_path / "o.docx")]) == 1
    assert "humanizer" in capsys.readouterr().out


def test_solo_lint_no_crea_documento(uc, datos_uc, tmp_path):
    cli.ejecutar(uc.TIPO, [escribir(tmp_path, limpiar_pendientes(datos_uc)), "--solo-lint",
                           "--salida", str(tmp_path / "o.docx")])
    assert not (tmp_path / "o.docx").exists()


@pytest.mark.parametrize("texto,regla,nivel", [
    ("El sistema debe de enviar avisos.", "C3", BLOQUEA),
    ("Muestra nombre, correo, etc.", "ABIERTO", BLOQUEA),
    ("Acepta PDF y/o JPG.", "ABIERTO", BLOQUEA),
    ("Incluye reportes, entre otros.", "ABIERTO", BLOQUEA),
    ("Se envía según corresponda.", "ABIERTO", BLOQUEA),
    ("En lo posible se valida.", "EVASIVA", BLOQUEA),
    ("Se envía cuando sea necesario.", "EVASIVA", BLOQUEA),
    ("Cabe destacar que registra pagos.", "IA-RELLENO", BLOQUEA),
    ("Es importante señalar que existe.", "IA-RELLENO", BLOQUEA),
    ("En resumen, registra pagos.", "IA-RELLENO", BLOQUEA),
    ("No solo registra sino también avisa.", "IA-CONTRASTE", BLOQUEA),
    ("Registra el pago — y avisa.", "IA-RAYA", BLOQUEA),
    ("La interfaz es intuitiva.", "SUBJETIVO", AVISA),
    ("Un proceso eficiente.", "IA-PALABRA", AVISA),
])
def test_prohibiciones_comunes(texto, regla, nivel):
    hallazgos = lint.revisar([Campo("x", texto)], lint.REGLAS_COMUNES)
    assert any(h.regla == regla and h.nivel == nivel for h in hallazgos)


def test_hallazgo_nombra_campo_fragmento_y_regla():
    h = lint.revisar([Campo("contenido.descripcion", "Cabe destacar que sí.")], lint.REGLAS_COMUNES)[0]
    assert "contenido.descripcion" in str(h) and "Cabe destacar" in str(h) and "IA-RELLENO" in str(h)


def test_lint_no_mira_dentro_de_pendientes():
    assert not lint.revisar([Campo("x", "[PENDIENTE: etc.]")], lint.REGLAS_COMUNES)


def test_debe_sin_de_no_bloquea():
    assert not lint.bloqueos(lint.revisar([Campo("x", "El Sistema deberá enviar avisos.")], lint.REGLAS_COMUNES))


def test_falta_soffice(uc, datos_uc, tmp_path, monkeypatch, capsys):
    real = render.shutil.which
    monkeypatch.setattr(render.shutil, "which", lambda h: None if h == "soffice" else real(h))
    salida_doc = tmp_path / "o.docx"
    d = limpiar_pendientes(datos_uc)
    assert cli.ejecutar(uc.TIPO, [escribir(tmp_path, d), "--salida", str(salida_doc)]) == 1
    assert "LibreOffice" in capsys.readouterr().err
    assert not salida_doc.exists()


def test_no_sobrescribe_sin_opcion(uc, datos_uc, tmp_path):
    destino = tmp_path / "o.docx"
    destino.write_text("original", encoding="utf-8")
    d = limpiar_pendientes(datos_uc)
    assert cli.ejecutar(uc.TIPO, [escribir(tmp_path, d), "--salida", str(destino)]) == 1
    assert destino.read_text(encoding="utf-8") == "original"


def test_fallo_de_verificacion_deja_intacto_el_destino(uc, datos_uc, tmp_path, monkeypatch):
    destino = tmp_path / "o.docx"
    destino.write_text("original", encoding="utf-8")
    monkeypatch.setattr(verificar, "comprobar", lambda *a: ["resto de plantilla"])
    d = limpiar_pendientes(datos_uc)
    assert cli.ejecutar(uc.TIPO, [escribir(tmp_path, d), "--salida", str(destino), "--sobrescribir"]) == 1
    assert destino.read_text(encoding="utf-8") == "original"


def test_pdf_opcional(uc, datos_uc, tmp_path):
    destino = tmp_path / "o.docx"
    d = limpiar_pendientes(datos_uc)
    assert cli.ejecutar(uc.TIPO, [escribir(tmp_path, d), "--salida", str(destino), "--pdf"]) == 0
    assert destino.exists() and destino.with_suffix(".pdf").exists()


def test_verificacion_detecta_texto_guia():
    problemas = verificar.comprobar(["[Descripción del requisito.]"], ["[Descripción del requisito.]"], [])
    assert problemas and "Texto guía" in problemas[0]


def test_verificacion_detecta_marcador_y_etiqueta():
    assert verificar.comprobar(["<Nombre del proyecto>"], [], [])
    assert verificar.comprobar(["Revision History"], [], [r"\bRevision History\b"])


def test_verificacion_limpia():
    assert verificar.comprobar(["Historial de revisiones"], ["[Guía larga de prueba]"], [r"\bRevision\b"]) == []


def test_localizar_ignora_lineas_de_indice():
    entradas = [render.Entrada("1.", "Introducción", 1, "a"), render.Entrada("1.1", "Objetivo", 2, "b")]
    paginas = ["1. Introducción ........ 4\n  1.1 Objetivo        4\n", "otra", "", "1.  Introducción\n1.1   Objetivo\n"]
    assert render.localizar(entradas, paginas) == {"a": 4, "b": 4}


def test_localizar_falla_si_falta_un_titulo():
    with pytest.raises(render.ErrorGeneracion):
        render.localizar([render.Entrada("9.", "No existe", 1, "a")], ["texto"])


def test_mover_crea_carpeta(tmp_path):
    origen = tmp_path / "a"
    origen.write_text("x", encoding="utf-8")
    salida.mover(origen, tmp_path / "sub" / "b")
    assert (tmp_path / "sub" / "b").read_text(encoding="utf-8") == "x"


def test_toda_fuente_citada_existe():
    import re
    from conftest import SKILLS
    tabla = (SKILLS / "_rup-comun" / "reglas-comunes.md").read_text(encoding="utf-8")
    definidas = set(re.findall(r"^\| (F\d+) \|", tabla, re.M))
    archivos = [SKILLS / "_rup-comun" / "reglas-comunes.md", *SKILLS.glob("rup-*/references/*.md")]
    citadas = {f for a in archivos for f in re.findall(r"\bF\d+\b", a.read_text(encoding="utf-8"))}
    assert citadas <= definidas and len(definidas) == 17


def test_rasgos_de_ia_documentados():
    from conftest import SKILLS
    guia = (SKILLS / "_rup-comun" / "redaccion-humanizada.md").read_text(encoding="utf-8")
    ids = {r.id for r in lint.REGLAS_COMUNES if r.id.startswith("IA-")}
    assert ids and all(i in guia for i in ids)


def test_skills_y_libreria():
    from conftest import SKILLS
    assert not (SKILLS / "_rup-comun" / "SKILL.md").exists()
    for s in ("rup-caso-de-uso", "rup-especificacion-suplementaria", "rup-glosario"):
        texto = (SKILLS / s / "SKILL.md").read_text(encoding="utf-8")
        assert texto.startswith(f"---\nname: {s}\n") and "negative-prompt.md" in texto and "humanizer" in texto


def test_lector_docx_sin_libreoffice(uc, datos_uc, tmp_path, monkeypatch):
    import importlib.util
    from conftest import SKILLS
    destino = tmp_path / "o.docx"
    assert cli.ejecutar(uc.TIPO, [escribir(tmp_path, limpiar_pendientes(datos_uc)), "--salida", str(destino)]) == 0
    spec = importlib.util.spec_from_file_location("leer_docx", SKILLS / "_rup-comun" / "leer_docx.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    monkeypatch.setattr(render.shutil, "which", lambda h: None)
    texto = modulo.lineas(destino)
    assert "4. El Sistema valida los datos obligatorios." in [t.strip() for t in texto]
    assert "a. Nombre completo" in [t.strip() for t in texto]
