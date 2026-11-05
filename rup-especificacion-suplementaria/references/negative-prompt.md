# Negative prompt: Especificación Suplementaria

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

## Especificación Suplementaria

```text
NO escribas un requisito sin "deberá" o sin uno de los cinco patrones.
NO metas dos requisitos en una sentencia.
NO copies flujos de casos de uso.
NO uses superlativos ni comparativos sin referencia: "el mejor", "más rápido".
NO uses términos sin cifra o criterio: "alta disponibilidad", "tiempo razonable".
NO uses "crítico", "seguro" o "adecuado" sin definirlos.
NO redactes la capacidad en negativo si puedes decir qué hace el sistema.
NO inventes umbrales: marca [PENDIENTE: ...].
```

| Prohibición | Control | Fuente |
|---|---|---|
| Requisito sin "deberá" | Bloquea | F13 |
| Superlativos, comparativos, términos vagos | Avisa | F11 |
| Negativos | Avisa | F11 |
| Dos requisitos en uno | Manual | F13 |
