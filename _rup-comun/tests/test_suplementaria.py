import pytest
from conftest import escribir, limpiar_pendientes

from rup_comun import cli, entrada, lint, verificar
from rup_comun.lint import AVISA, BLOQUEA


def errores(s, datos):
    with pytest.raises(entrada.ErrorEntrada) as e:
        cli.validar_entrada(s.TIPO, datos)
    return "\n".join(e.value.errores)


def con_requisito(datos, seccion, texto):
    datos["contenido"][seccion] = {"requisitos": [{"titulo": "R", "descripcion": texto}]}
    return datos


def test_trece_secciones_en_orden(supl, datos_supl):
    doc = supl.construir(limpiar_pendientes(datos_supl))
    titulos = [e.titulo for e in doc.indice if e.nivel == 1]
    assert titulos == ["Introducción", "Funcionalidad", "Usabilidad", "Confiabilidad", "Desempeño", "Soporte",
                       "Restricciones de diseño",
                       "Requisitos del sistema de documentación y ayuda para el usuario en línea",
                       "Componentes adquiridos", "Interfaces", "Requisitos de licencia",
                       "Avisos legales, de derechos de autor y otros avisos", "Normas aplicables"]


def generar(s, datos, tmp_path):
    destino = tmp_path / "o.docx"
    assert cli.ejecutar(s.TIPO, [escribir(tmp_path, limpiar_pendientes(datos)), "--salida", str(destino)]) == 0
    return verificar.textos_docx(destino)


def test_titulo_normalizado_y_anio(supl, datos_supl, tmp_path):
    textos = " ".join(generar(supl, datos_supl, tmp_path))
    assert "complementaria" not in textos.lower()
    assert "2001" not in textos and "2026" in textos


def test_no_aplica_y_remision_al_glosario(supl, datos_supl, tmp_path):
    textos = generar(supl, datos_supl, tmp_path)
    assert "No aplica." in textos
    assert "Las definiciones se encuentran en el Glosario del proyecto." in textos
    assert "Casos de uso relacionados: Realizar pago de renta." in textos


def test_seccion_omitida(supl, datos_supl):
    del datos_supl["contenido"]["normas"]
    assert "contenido.normas" in errores(supl, datos_supl)


def test_seccion_sin_contenido_ni_no_aplica(supl, datos_supl):
    datos_supl["contenido"]["licencia"] = {}
    assert "contenido.licencia" in errores(supl, datos_supl)


def test_contenido_y_no_aplica_a_la_vez(supl, datos_supl):
    datos_supl["contenido"]["licencia"] = {"texto": ["x"], "no_aplica": True}
    assert "deja uno solo" in errores(supl, datos_supl)


def test_requisito_sin_descripcion(supl, datos_supl):
    datos_supl["contenido"]["desempeno"]["requisitos"][0].pop("descripcion")
    assert "desempeno.requisitos[0].descripcion" in errores(supl, datos_supl)


def test_requisitos_numerados(supl, datos_supl):
    d = limpiar_pendientes(datos_supl)
    d["contenido"]["desempeno"]["requisitos"] = [
        {"titulo": t, "descripcion": "El Sistema deberá registrar el dato."} for t in "ABC"]
    doc = supl.construir(d)
    assert [e.numero for e in doc.indice if e.titulo in "ABC"] == ["5.1", "5.2", "5.3"]


@pytest.mark.parametrize("texto", [
    "El Sistema deberá registrar cada inicio de sesión.",
    "Cuando se registre un pago, el Sistema deberá generar el recibo.",
    "Mientras exista un cobro vencido, el Sistema deberá mostrar su estado.",
    "Si falla el envío del correo, entonces el Sistema deberá registrar el error.",
    "Donde exista firma electrónica, el Sistema deberá guardar la constancia.",
])
def test_patrones_ears_sin_hallazgos(supl, datos_supl, texto):
    d = con_requisito(datos_supl, "soporte", texto)
    assert not [h for h in cli.revisar(supl.TIPO, d) if "soporte" in h.ruta]


@pytest.mark.parametrize("texto,regla,nivel", [
    ("El Sistema registra el pago.", "S3", BLOQUEA),
    ("En lo posible, el Sistema deberá validar los archivos.", "EVASIVA", BLOQUEA),
    ("El Sistema deberá ofrecer la mejor respuesta.", "S-SUPERLATIVO", AVISA),
    ("El Sistema deberá ser más estable.", "S-COMPARATIVO", AVISA),
    ("El Sistema no deberá cerrar la sesión.", "S-NEGATIVO", AVISA),
    ("El Sistema deberá atender fallos críticos.", "S7", AVISA),
    ("El módulo deberá registrar el pago.", "S4", AVISA),
    ("Si falla el pago, el Sistema deberá avisar.", "S4", AVISA),
])
def test_prohibiciones_de_requisitos(supl, datos_supl, texto, regla, nivel):
    d = con_requisito(datos_supl, "soporte", texto)
    assert any(h.regla == regla and h.nivel == nivel for h in cli.revisar(supl.TIPO, d))


def test_termino_vago_sin_cifra(supl, datos_supl):
    d = con_requisito(datos_supl, "desempeno", "El Sistema deberá responder rápido.")
    assert any(h.regla == "S-MEDIBLE" and h.nivel == AVISA for h in cli.revisar(supl.TIPO, d))


def test_requisito_medible_sin_aviso(supl, datos_supl):
    d = con_requisito(datos_supl, "desempeno", "El Sistema deberá responder en 2 segundos.")
    assert not [h for h in cli.revisar(supl.TIPO, d) if h.regla == "S-MEDIBLE"]


def test_salida_por_defecto(supl, datos_supl):
    assert str(supl.TIPO.salida_por_defecto(datos_supl)) == "docs/Especificacion Suplementaria.docx"


def test_ejemplo_sin_bloqueos_de_lint(supl, datos_supl):
    assert lint.bloqueos(cli.revisar(supl.TIPO, datos_supl)) == []
