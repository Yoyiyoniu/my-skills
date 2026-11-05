# Negative prompt: Glosario

Carga este archivo antes de redactar. **Bloquea** = el lint impide la versión final. **Avisa** = advertencia. **Manual** = la skill lo revisa, porque una expresión regular no lo detecta bien.

## Para todos los documentos

```text
NO copies la redacción de los UCS en docs/. Úsalos solo como fuente de hechos.
NO inventes actores, reglas, cifras, normas, autores ni fechas.
NO uses "debe de" ni "deberá de".
NO uses "etc.", "y/o", "entre otros" ni "según corresponda".
NO uses sinónimos para variar: un concepto, un nombre.
NO uses frases de relleno como "cabe destacar", "es importante señalar" o "en resumen".
NO uses lenguaje subjetivo: fácil, amigable, intuitivo, rápido, simple, moderno.
NO uses evasivas: "en lo posible", "cuando sea necesario", "de ser posible".
NO dejes referencias que no se puedan seguir.
```

| Prohibición | Control | Regla |
|---|---|---|
| "debe de" | Bloquea | C3 |
| "etc.", "y/o", "entre otros" | Bloquea | F11 (términos abiertos) |
| Relleno de IA | Bloquea | Lint, `humanizer` |
| Evasivas | Bloquea | F11 (loopholes) |
| Lenguaje subjetivo | Avisa | F11 |
| Sinónimos | Manual | C2 |

## Glosario

```text
NO definas un término con él mismo.
NO empieces con "es cuando", "se refiere a" o "es un término que".
NO definas por lo que el término no es.
NO definas A con B y B con A.
NO escribas más de un párrafo por término.
NO copies una definición general si el término significa otra cosa en SGP.
NO repitas un término con otro nombre: usa una entrada y remite a ella.
```

| Prohibición | Control | Fuente |
|---|---|---|
| Definición con el mismo término | Avisa | F16 |
| Apertura "es cuando", "se refiere a" | Avisa | G1 |
| Definición negativa | Avisa | F16, nivel C: solo aparece en el borrador ISO/DIS 704 |
| A y B definidos entre sí | Avisa | F16 |
| Más de un párrafo | Bloquea | G6 |
