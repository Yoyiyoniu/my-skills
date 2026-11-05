import zipfile

import pytest
from conftest import escribir, limpiar_pendientes

from rup_comun import cli, entrada, lint, verificar
from rup_comun.lint import AVISA


def errores(g, datos):
    with pytest.raises(entrada.ErrorEntrada) as e:
        cli.validar_entrada(g.TIPO, datos)
    return "\n".join(e.value.errores)


def terminos(lista):
    return [{"termino": t, "definicion": d} for t, d in lista]


def generar(g, datos, tmp_path, *extra):
    destino = tmp_path / "o.odt"
    assert cli.ejecutar(g.TIPO, [escribir(tmp_path, datos), "--salida", str(destino), *extra]) == 0
    return destino


def test_orden_alfabetico_espanol(glos):
    nombres = ["Ñandú", "Área", "Nómina", "Arrendador"]
    assert sorted(nombres, key=glos.clave_orden) == ["Área", "Arrendador", "Nómina", "Ñandú"]


def test_orden_no_depende_de_la_entrada(glos, datos_glos):
    d = limpiar_pendientes(datos_glos)
    a = [e.titulo for e in glos.construir(d).indice]
    d["contenido"]["terminos"].reverse()
    assert [e.titulo for e in glos.construir(d).indice] == a


def test_numeracion_de_grupos(glos, datos_glos):
    indice = glos.construir(limpiar_pendientes(datos_glos)).indice
    assert ("2.4", "Cobranza") in [(e.numero, e.titulo) for e in indice]
    assert ("2.4.1", "Cobro vencido") in [(e.numero, e.titulo) for e in indice]


def test_estructura(glos, datos_glos):
    indice = glos.construir(limpiar_pendientes(datos_glos)).indice
    assert [e.titulo for e in indice if e.nivel == 1] == ["Introducción", "Definiciones", "Estereotipos UML"]
    assert [e.titulo for e in indice[1:5]] == ["Propósito", "Alcance", "Referencias", "Descripción general"]


def test_duplicado_sin_distinguir_mayusculas_ni_acentos(glos, datos_glos):
    datos_glos["contenido"]["terminos"].append({"termino": "inmueble", "definicion": "Otro."})
    assert "inmueble" in errores(glos, datos_glos)


def test_duplicado_entre_grupos(glos, datos_glos):
    datos_glos["contenido"]["grupos"][0]["terminos"].append({"termino": "Inmueble", "definicion": "Otro."})
    assert "repetido" in errores(glos, datos_glos)


def test_sin_terminos(glos, datos_glos):
    datos_glos["contenido"]["terminos"] = []
    datos_glos["contenido"]["grupos"] = []
    assert "al menos un término" in errores(glos, datos_glos)


@pytest.mark.parametrize("termino,definicion,regla", [
    ("Recibo", "Recibo del sistema.", "G-CIRCULAR"),
    ("Pago", "Es cuando el Arrendatario entrega dinero.", "G1-APERTURA"),
    ("Pago", "Se refiere a la entrega de dinero.", "G1-APERTURA"),
    ("Pago", "No es un cobro pendiente.", "G-NEGATIVA"),
])
def test_avisos_de_definicion(glos, datos_glos, termino, definicion, regla):
    datos_glos["contenido"]["terminos"] = terminos([(termino, definicion)])
    datos_glos["contenido"]["grupos"] = []
    assert any(h.regla == regla and h.nivel == AVISA for h in cli.revisar(glos.TIPO, datos_glos))


def test_pares_mutuos(glos, datos_glos):
    datos_glos["contenido"]["terminos"] = terminos([("Cobro", "Monto que genera un Recibo."),
                                                    ("Recibo", "Comprobante de un Cobro.")])
    datos_glos["contenido"]["grupos"] = []
    assert any(h.regla == "G-MUTUA" for h in cli.revisar(glos.TIPO, datos_glos))


def test_reutilizar_en_una_direccion_no_avisa(glos, datos_glos):
    datos_glos["contenido"]["terminos"] = terminos([("Cobro", "Monto que debe pagar una persona."),
                                                    ("Recibo", "Comprobante de un Cobro.")])
    datos_glos["contenido"]["grupos"] = []
    assert not [h for h in cli.revisar(glos.TIPO, datos_glos) if h.regla in ("G-MUTUA", "G-CIRCULAR")]


def test_mas_de_un_parrafo_bloquea(glos, datos_glos):
    datos_glos["contenido"]["terminos"] = terminos([("Pago", "Entrega de dinero.\n\nOtro párrafo.")])
    assert any(h.regla == "G6" for h in lint.bloqueos(cli.revisar(glos.TIPO, datos_glos)))


def test_salida_por_defecto(glos, datos_glos):
    assert str(glos.TIPO.salida_por_defecto(datos_glos)) == "docs/Glosario.odt"


def test_odt_valido_y_en_espanol(glos, datos_glos, tmp_path):
    destino = generar(glos, limpiar_pendientes(datos_glos), tmp_path)
    with zipfile.ZipFile(destino) as z:
        assert z.namelist()[0] == "mimetype"
        assert z.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        assert "Thumbnails/thumbnail.png" not in z.namelist()
    textos = " ".join(verificar.textos_odt(destino))
    assert "No se definieron estereotipos adicionales." in textos
    assert "Inmobiliaria Moach" in textos and "BugLabs" in textos and "2026" in textos


def test_portada_conserva_nombre_marcado_como_pendiente(glos, datos_glos, tmp_path):
    destino = generar(glos, datos_glos, tmp_path, "--borrador")
    assert "[PENDIENTE: nombre oficial del proyecto]" in verificar.textos_odt(destino)


def test_ejemplo_sin_bloqueos_de_lint(glos, datos_glos):
    assert lint.bloqueos(cli.revisar(glos.TIPO, datos_glos)) == []
