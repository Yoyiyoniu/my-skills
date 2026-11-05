"""Lint de redacción en español. Las reglas salen del negative prompt.

Un hallazgo es una señal a revisar: BLOQUEA solo lo que casi nunca es legítimo.
"""
import re
from dataclasses import dataclass

from .entrada import PENDIENTE

BLOQUEA = "bloquea"
AVISA = "avisa"


@dataclass(frozen=True)
class Campo:
    ruta: str
    texto: str
    clase: str = "prosa"  # prosa, paso, requisito, definicion


@dataclass(frozen=True)
class Regla:
    id: str
    patron: str
    nivel: str
    mensaje: str
    clases: tuple = ()  # vacío: se aplica a todas las clases


@dataclass(frozen=True)
class Hallazgo:
    ruta: str
    fragmento: str
    regla: str
    mensaje: str
    nivel: str

    def __str__(self):
        return f"[{self.regla}] {self.ruta}: «{self.fragmento}». {self.mensaje}"


REGLAS_COMUNES = [
    Regla("C3", r"\bdeb(?:e|en|erá|erán|ía|ían)\s+de\b", BLOQUEA,
          "La obligación se escribe sin «de»: «debe» o «deberá»."),
    Regla("ABIERTO", r"\betc\b\.?|\by/o\b|\bentre otros\b|\bentre otras\b|\bsegún corresponda\b", BLOQUEA,
          "Término abierto: enumera los casos."),
    Regla("EVASIVA", r"\ben (?:la medida de )?lo posible\b|\bcuando sea necesario\b|\bde ser posible\b"
                     r"|\bsi es posible\b|\bsiempre que sea posible\b", BLOQUEA,
          "Evasiva: indica la condición exacta."),
    Regla("IA-RELLENO", r"\bcabe (?:destacar|señalar|mencionar|resaltar)\b"
                        r"|\bes importante (?:destacar|señalar|mencionar|resaltar|notar)\b"
                        r"|\ben resumen\b|\ben conclusión\b|\bsin duda\b"
                        r"|\ben el mundo actual\b|\bjuega un papel\b|\bdesempeña un papel\b", BLOQUEA,
          "Relleno propio de texto de IA: elimínalo y di el hecho."),
    Regla("IA-CONTRASTE", r"\bno s[oó]lo\b[^.]*\bsino\b", BLOQUEA,
          "Contraste «no solo... sino»: di los dos hechos directamente."),
    Regla("IA-RAYA", r"—", BLOQUEA, "Raya usada como conector: usa punto o coma."),
    Regla("SUBJETIVO", r"\b(?:fácil(?:es)?|amigable(?:s)?|intuitiv[oa]s?|rápid[oa]s?|sencill[oa]s?"
                       r"|simples?|modern[oa]s?)\b", AVISA,
          "Lenguaje subjetivo: da un criterio verificable."),
    Regla("IA-PALABRA", r"\b(?:eficiente(?:s)?|eficientemente|robust[oa]s?|integral(?:es)?|optimizar"
                        r"|optimiza|garantizar|garantiza)\b", AVISA,
          "Palabra frecuente en texto de IA: confirma que aporta un hecho."),
]


def revisar(campos, reglas):
    """Aplica `reglas` a cada campo, sin mirar dentro de los marcadores pendientes."""
    hallazgos = []
    for campo in campos:
        texto = PENDIENTE.sub(" ", campo.texto)
        for regla in reglas:
            if regla.clases and campo.clase not in regla.clases:
                continue
            for m in re.finditer(regla.patron, texto, re.IGNORECASE):
                hallazgos.append(Hallazgo(campo.ruta, m.group(0), regla.id, regla.mensaje, regla.nivel))
        if len(re.findall(r"\bde manera\b", texto, re.IGNORECASE)) >= 2:
            hallazgos.append(Hallazgo(campo.ruta, "de manera", "IA-PALABRA",
                                      "«de manera» repetido: usa el verbo directo.", AVISA))
    return hallazgos


def bloqueos(hallazgos):
    return [h for h in hallazgos if h.nivel == BLOQUEA]


def avisos(hallazgos):
    return [h for h in hallazgos if h.nivel == AVISA]
