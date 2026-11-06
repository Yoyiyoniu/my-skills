---
name: rup-glosario
description: Redacta y genera el Glosario del proyecto en .odt sobre la plantilla RUP, con definiciones por categoría y rasgos, orden alfabético en español, grupos de términos, negative prompt, lint en español y paso obligatorio por humanizer. Usar cuando el usuario pida crear, ampliar o redactar el glosario, definir términos del dominio o unificar la terminología de los documentos.
---

# Glosario

Produce el glosario único del sistema: una definición por término, basada en lo que dicen los documentos del proyecto.

## Antes de redactar

Lee estos archivos, en este orden:

0. `preguntas-respuestas.md`, junto al JSON, si ya existe: lo que el usuario ya respondió. Es obligatorio.
1. `references/negative-prompt.md`: qué no escribir. Es obligatorio.
2. `references/reglas-redaccion.md`: cómo se escribe cada sentencia.
3. `references/guia-secciones.md`: qué va en cada sección y el contrato del JSON.
4. `../_rup-comun/redaccion-humanizada.md`: cómo usar `humanizer`.
5. `../_rup-comun/reglas-comunes.md`: fuentes y conflictos, cuando dudes de una regla.

## Reglas que no se negocian

- **Los documentos de `docs/` no son modelo.** Su redacción es incorrecta: úsalos solo para obtener hechos.
- **Nada se inventa.** Actores, reglas, cifras, normas, autores y fechas vienen del usuario o de sus documentos. Lo demás es `[PENDIENTE: qué falta]`.
- **Si dos documentos se contradicen, pregunta.** No elijas por tu cuenta. El nombre del sistema aparece como "Gestión de Propiedades" y "Gestión de Inmuebles": confírmalo con el usuario.
- **Cada pregunta y respuesta se guarda.** Usa `preguntas-respuestas.md`, con la sección `## Glosario`, como indica `../_rup-comun/registro-preguntas.md`. Sus respuestas prevalecen sobre cualquier documento y no se vuelven a preguntar.
- **Cada edición se confirma.** Antes de generar, sugiere al usuario la fecha, la versión, la descripción y el autor de esta edición, y pide su confirmación. Una sugerencia sin confirmar no vale.
- **`humanizer` es obligatorio** antes de una versión final.

## Leer los documentos existentes

Lee los `.docx` con Python. No uses LibreOffice ni `soffice` para abrirlos: `docs/UCS Firmar contratos.docx`, por ejemplo, no carga ahí. Desde la raíz del repositorio:

```bash
uv run .claude/skills/_rup-comun/leer_docx.py "docs/<documento>.docx"
```

## Flujo

Cada vez que el usuario responda, guarda la pregunta y su respuesta textual en el registro antes de seguir.

1. **Extrae candidatos** de los UCS como indica `references/guia-secciones.md` y preséntalos al usuario antes de redactar definiciones.
2. **Redacta el JSON** en un archivo fuera de `docs/`, con `assets/ejemplo.json` como modelo.
3. **Revisa** desde la raíz del repositorio:
   ```bash
   uv run .claude/skills/rup-glosario/scripts/generar.py entrada.json --solo-lint
   ```
   Corrige los bloqueos y revisa cada aviso.
4. **Invoca la skill `humanizer`** como indica `redaccion-humanizada.md`. Después pon `redaccion.humanizer_aplicado: true`.
5. **Vuelve a revisar** con `--solo-lint`: `humanizer` no debe haber cambiado nada protegido.
6. **Confirma la edición.** Presenta una sugerencia para la fecha, la versión, la descripción y el autor, como indica `../_rup-comun/registro-preguntas.md`, y pide confirmarlas o cambiarlas. Guarda las respuestas en el registro, añade la revisión al `historial` y pon `redaccion.revision_confirmada: true`. `--solo-lint` muestra la edición que quedará en el documento.
7. **Genera:**
   ```bash
   uv run .claude/skills/rup-glosario/scripts/generar.py entrada.json
   ```
   El documento queda en `docs/Glosario.odt`.
8. **Informa** de los avisos que queden y de los datos que confirmaste. Recuerda que el índice se actualiza con F9 si el equipo abre el documento en Word.

Si aún hay pendientes, genera un borrador y dilo con claridad:

```bash
uv run .claude/skills/rup-glosario/scripts/generar.py entrada.json --borrador
```

## Opciones

| Opción | Efecto |
|---|---|
| `--salida RUTA` | Escribe en otra ruta |
| `--borrador` | Admite pendientes, bloqueos del lint y falta de registro; no es una versión final |
| `--sobrescribir` | Reemplaza un archivo existente, que por defecto se protege |
| `--pdf` | Deja también una copia en PDF |
| `--registro RUTA` | Usa otro registro de preguntas y respuestas |
| `--solo-lint` | Revisa sin crear ningún documento |

Requiere `uv`, LibreOffice (`soffice`) y `pdftotext`. Las páginas del índice se calculan con LibreOffice: en Word pueden diferir, y se actualizan con F9.
