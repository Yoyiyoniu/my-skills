# Negative prompt: Caso de uso

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

## Caso de uso

```text
NO empieces un paso con algo distinto de un actor registrado o "El Sistema".
NO escribas condiciones en el flujo básico: "Si...", "En caso de...", "Cuando...".
NO uses "puede", "podrá", "debería", "opcionalmente" en un paso.
NO describas clics, botones, pantallas ni menús.
NO menciones base de datos, tablas, API, servidor o código.
NO uses pasiva ni impersonal: "es registrado", "se registra".
NO uses adverbios de relleno: "correctamente", "exitosamente", "automáticamente".
NO uses pronombres cuando haya más de un actor.
NO juntes dos acciones en un paso.
NO escribas "ingresa sus datos" o "la información" si se conocen los datos.
NO dejes un flujo alterno sin inicio o con dos desenlaces: "continúa o finaliza".
NO escribas "El Sistema verifica si...": escribe "El Sistema valida...".
NO uses precondiciones ni postcondiciones para encadenar casos de uso.
NO uses IF-THEN-ELSE ni bucles con forma de código.
NO describas lo que ocurre en otros casos de uso.
```

| Forma incorrecta (en `docs/`) | Forma correcta | Regla | Control |
|---|---|---|---|
| 7. Si el cobro se encuentra pendiente o vencido, el sistema muestra la opción... | Pasa a un flujo alterno con su condición | U15 | Bloquea |
| El administrador puede seleccionar la opción... | Flujo alterno con la condición que lo activa | U3, U15 | Bloquea |
| El Cliente potencial hace clic en "Aceptar"... | El Cliente potencial envía la solicitud. | U6 | Bloquea |
| ...fue registrada correctamente. | ...quedó registrada. | Reglas de adverbios F1, F7 | Bloquea |
| El Sistema verifica que los datos obligatorios hayan sido proporcionados. | El Sistema valida los datos obligatorios. | U5 | Avisa |
| El caso de uso continúa con la consulta del cobro o finaliza. | Un único desenlace | U13 | Bloquea por dato: el JSON solo admite uno |
| Cliente / potencial cliente / Cliente potencial | Cliente potencial | U9 | Bloquea: el actor debe estar registrado |
| Paso con base de datos, API o SQL | Lo que el sistema hace para el actor | U8 | Bloquea |
| Pasiva o "se registra" | El Sistema registra... | U3 | Bloquea: el paso no empieza por un actor registrado |
| Más de 9 pasos | Dividir en subflujos | U10 | Avisa |
| Pronombres, negación en flujo básico | Nombre completo o flujo alterno | F7, U16 | Avisa |
| Dos acciones en un paso | Dos pasos | U3 | Manual |
