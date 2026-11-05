# Redacción con humanizer

Todo texto de estos documentos pasa por la skill `humanizer` antes de la versión final. Un script no puede invocar una skill, así que el paso lo hace el agente.

## Flujo

1. **Redactar.** Escribe el JSON siguiendo las reglas y el negative prompt. Lo que falte queda como `[PENDIENTE: qué falta]`.
2. **Humanizar.** Invoca `humanizer` en modo embebido sobre los campos en prosa. Pásale como muestra de voz `assets/ejemplo.json` de la skill, y nunca un documento de `docs/`.
3. **Declarar.** Pon `"redaccion": { "humanizer_aplicado": true }` en el JSON.
4. **Comprobar.** Ejecuta `generar.py` con `--solo-lint` y corrige lo que bloquee.

La marca solo declara que hiciste el paso y no lo prueba. No la pongas si no invocaste `humanizer`.

## Qué pasa por humanizer

| Campo | Trato |
|---|---|
| Descripciones, objetivo, alcance, introducciones, descripción general | Pasan por `humanizer` |
| Texto de secciones 8 a 13 de la Suplementaria | Pasan por `humanizer` |
| Condiciones de flujos alternos, definiciones | Pasan por `humanizer` conservando la forma de su regla |
| Pasos de flujos y sentencias de requisitos | Solo revisión de rasgos: conservan su forma fija |

## Contenido protegido

`humanizer` no cambia: numeración de pasos, referencias entre pasos, identificadores, nombres de actores, nombres de campos, etiquetas, cifras, verbos normativos ("deberá") ni marcadores `[PENDIENTE: ...]`.

Después del paso, compara antes y después: mismo número de pasos, mismo orden, mismos actores y ningún nombre, cifra, fecha o afirmación nueva.

## Reglas de humanizer que no aplican

- **§7, aperturas repetidas.** "El Sistema..." se repite a propósito: es el diálogo actor-sistema de RUP.
- **§11, voz pasiva y sujetos ausentes.** En requisitos normativos manda el patrón de la regla.
- **Variar la longitud de las frases.** Vale para la prosa libre. En pasos, requisitos y definiciones manda la forma fija.

Si `humanizer` y una regla de redacción piden cosas distintas, gana la regla.

## Rasgos de IA que revisa el lint

| Regla | Ejemplos | Efecto |
|---|---|---|
| IA-RELLENO | "cabe destacar", "es importante señalar", "en resumen", "en conclusión", "sin duda", "en el mundo actual", "juega un papel" | Bloquea |
| IA-CONTRASTE | "no solo ... sino" | Bloquea |
| IA-RAYA | "—" como conector | Bloquea |
| IA-PALABRA | "eficiente", "robusto", "integral", "optimizar", "garantizar", "de manera" repetido | Avisa |

Un aviso pide revisar el texto y no siempre indica un error: un término técnico legítimo puede activarlo.
