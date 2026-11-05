import pytest
from conftest import escribir, limpiar_pendientes

from rup_comun import cli, docx_util as du, entrada, lint, verificar
from rup_comun.lint import AVISA, BLOQUEA


def errores(uc, datos):
    with pytest.raises(entrada.ErrorEntrada) as e:
        cli.validar_entrada(uc.TIPO, datos)
    return "\n".join(e.value.errores)


def hallazgo_paso(uc, datos, texto, lista="flujo_basico"):
    datos["contenido"]["flujo_basico"][1]["paso"] = texto
    return cli.revisar(uc.TIPO, datos)


def test_ejemplo_sin_bloqueos_de_lint(uc, datos_uc):
    assert lint.bloqueos(cli.revisar(uc.TIPO, datos_uc)) == []


def test_paso_inexistente(uc, datos_uc):
    datos_uc["contenido"]["flujos_alternos"][0]["regresa_a_paso"] = 12
    e = errores(uc, datos_uc)
    assert "Datos incompletos" in e and "12" in e


def test_flujo_sin_desenlace(uc, datos_uc):
    del datos_uc["contenido"]["flujos_alternos"][0]["regresa_a_paso"]
    assert "no indica cómo termina" in errores(uc, datos_uc)


def test_dos_desenlaces(uc, datos_uc):
    datos_uc["contenido"]["flujos_alternos"][0]["finaliza"] = True
    assert "dos desenlaces" in errores(uc, datos_uc)


def test_inicio_ausente(uc, datos_uc):
    del datos_uc["contenido"]["inicio"]
    assert "contenido.inicio" in errores(uc, datos_uc)


def test_inicio_sin_actor(uc, datos_uc):
    datos_uc["contenido"]["inicio"] = "alguien pide una cita"
    assert "contenido.inicio" in errores(uc, datos_uc)


def test_actor_principal_no_registrado(uc, datos_uc):
    datos_uc["contenido"]["actor_principal"] = "Administrador"
    assert "actor_principal" in errores(uc, datos_uc)


def test_punto_extension_paso_inexistente(uc, datos_uc):
    datos_uc["contenido"]["puntos_extension"] = [{"nombre": "X", "paso": 40, "descripcion": "Y"}]
    assert "40" in errores(uc, datos_uc)


@pytest.mark.parametrize("texto,regla,nivel", [
    ("Si el cobro se encuentra vencido, el Sistema muestra la opción.", "U15", BLOQUEA),
    ("El Sistema muestra la opción, si el cobro está vencido.", "U15", BLOQUEA),
    ("El Cliente potencial puede seleccionar la opción.", "U3-OPCIONAL", BLOQUEA),
    ("El Cliente potencial hace clic en Aceptar.", "U6", BLOQUEA),
    ("El Sistema muestra la pantalla de pago.", "U6", BLOQUEA),
    ("El Sistema guarda la cita en la base de datos.", "U8", BLOQUEA),
    ("El Sistema llama a la API de pagos.", "U8", BLOQUEA),
    ("El Sistema informa que la solicitud fue registrada correctamente.", "ADVERBIO", BLOQUEA),
    ("El cliente proporciona su nombre.", "U9", BLOQUEA),
    ("Se registra la solicitud.", "U9", BLOQUEA),
    ("La solicitud es registrada.", "U9", BLOQUEA),
    ("El Sistema verifica que los datos obligatorios hayan sido proporcionados.", "U5", AVISA),
    ("El Sistema es actualizado por el proceso.", "U3-PASIVA", AVISA),
    ("El Sistema avisa a ella.", "PRONOMBRE", AVISA),
    ("El Sistema no registra la cita.", "U16", AVISA),
    ("El Cliente potencial proporciona sus datos.", "U7", AVISA),
])
def test_tabla_del_negative_prompt(uc, datos_uc, texto, regla, nivel):
    assert any(h.regla == regla and h.nivel == nivel for h in hallazgo_paso(uc, datos_uc, texto))


def test_paso_correcto_sin_hallazgos(uc, datos_uc):
    hallazgos = hallazgo_paso(uc, datos_uc, "El Sistema registra la solicitud de cita.")
    assert not [h for h in hallazgos if "flujo_basico[1]" in h.ruta]


def test_mas_de_nueve_pasos_avisa(uc, datos_uc):
    datos_uc["contenido"]["flujo_basico"] += [{"paso": "El Sistema registra el dato."}] * 5
    assert any(h.regla == "U10" and h.nivel == AVISA for h in cli.revisar(uc.TIPO, datos_uc))


def test_nombre_sin_infinitivo_avisa(uc, datos_uc):
    datos_uc["contenido"]["nombre"] = "Citas"
    assert any(h.regla == "U1" for h in cli.revisar(uc.TIPO, datos_uc))


def test_salida_por_defecto(uc, datos_uc):
    datos_uc["contenido"]["nombre"] = "Consultar contrato"
    assert str(uc.TIPO.salida_por_defecto(datos_uc)) == "docs/UCS Consultar contrato.docx"


def generar(uc, datos, tmp_path):
    destino = tmp_path / "o.docx"
    assert cli.ejecutar(uc.TIPO, [escribir(tmp_path, limpiar_pendientes(datos)), "--salida", str(destino)]) == 0
    return verificar.textos_docx(destino), destino


def test_lineas_fijas_y_seccion_vacia(uc, datos_uc, tmp_path):
    textos, _ = generar(uc, datos_uc, tmp_path)
    assert any(t.startswith("Este flujo comienza en el paso 4 del flujo básico cuando") for t in textos)
    assert "El flujo regresa al paso 2." in textos
    assert "No se identificaron puntos de extensión para este caso de uso." in textos
    assert any(t.startswith("Este caso de uso comienza cuando el Cliente potencial") for t in textos)


def test_cierre_del_flujo_basico(uc, datos_uc):
    assert uc.pasos_basicos(datos_uc["contenido"])[-1]["paso"] == uc.FIN


def test_indice_coincide_con_cuerpo(uc, datos_uc):
    doc = uc.construir(limpiar_pendientes(datos_uc))
    assert [e.numero for e in doc.indice][:3] == ["1.", "1.1", "2."]
    assert ("2.2.2", "Solicitud cancelada") in [(e.numero, e.titulo) for e in doc.indice]


def test_subflujo_numerado_nivel_cuatro_fuera_del_indice(uc, datos_uc):
    datos_uc["contenido"]["flujos_alternos"][0]["subflujos"] = [{
        "nombre": "Sub", "desde_paso": 4, "condicion": "falta la hora",
        "pasos": [{"paso": "El Sistema solicita la hora."}], "finaliza": True}]
    doc = uc.construir(limpiar_pendientes(datos_uc))
    assert "Sub" not in [e.titulo for e in doc.indice]


def test_marca_de_pagina_en_indice(uc, datos_uc, tmp_path):
    _, destino = generar(uc, datos_uc, tmp_path)
    import docx
    from docx.oxml.ns import qn
    d = docx.Document(str(destino))
    sdt = d.element.body.find(qn("w:sdt"))
    assert "TOC" in "".join(i.text or "" for i in sdt.iter(qn("w:instrText")))
    assert "0" not in [du.texto_de(p)[-1] for p in sdt.iter(qn("w:p"))]
