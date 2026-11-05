---
name: rup-caso-de-uso
description: Redacta y genera una Especificación de Caso de Uso (UCS) en .docx sobre la plantilla RUP del proyecto, con reglas de redacción respaldadas por fuentes, negative prompt, lint en español y paso obligatorio por humanizer. Usar cuando el usuario pida crear, redactar, rehacer o revisar un caso de uso o UCS, un flujo básico, flujos alternos, precondiciones o postcondiciones, aunque no mencione RUP.
---

# Especificación de Caso de Uso

Produce un documento con la plantilla RUP: flujos que se pueden seguir paso a paso y referencias que el script comprueba.

## Antes de redactar

Lee estos archivos, en este orden:

1. `references/negative-prompt.md`: qué no escribir. Es obligatorio.
2. `references/reglas-redaccion.md`: cómo se escribe cada sentencia.
3. `references/guia-secciones.md`: qué va en cada sección y el contrato del JSON.
4. `../_rup-comun/redaccion-humanizada.md`: cómo usar `humanizer`.
5. `../_rup-comun/reglas-comunes.md`: fuentes y conflictos, cuando dudes de una regla.

## Reglas que no se negocian

- **Los documentos de `docs/` no son modelo.** Su redacción es incorrecta: úsalos solo para obtener hechos.
- **Nada se inventa.** Actores, reglas, cifras, normas, autores y fechas vienen del usuario o de sus documentos. Lo demás es `[PENDIENTE: qué falta]`.
- **Si dos documentos se contradicen, pregunta.** No elijas por tu cuenta. El nombre del sistema aparece como "Gestión de Propiedades" y "Gestión de Inmuebles": confírmalo con el usuario.
- **`humanizer` es obligatorio** antes de una versión final.

## Leer los documentos existentes

Lee los `.docx` con Python. No uses LibreOffice ni `soffice` para abrirlos: `docs/UCS Firmar contratos.docx`, por ejemplo, no carga ahí. Desde la raíz del repositorio:

```bash
uv run .claude/skills/_rup-comun/leer_docx.py "docs/<documento>.docx"
```

## Flujo

1. **Reúne los hechos.** Pregunta lo que falte: actores, actor que inicia, objetivo, datos que se intercambian, excepciones y qué pasa tras cada una. Lee los UCS relacionados solo para sacar hechos.
2. **Redacta el JSON** en un archivo fuera de `docs/`, con `assets/ejemplo.json` como modelo.
3. **Revisa** desde la raíz del repositorio:
   ```bash
   uv run .claude/skills/rup-caso-de-uso/scripts/generar.py entrada.json --solo-lint
   ```
   Corrige los bloqueos y revisa cada aviso.
4. **Invoca la skill `humanizer`** como indica `redaccion-humanizada.md`. Después pon `redaccion.humanizer_aplicado: true`.
5. **Vuelve a revisar** con `--solo-lint`: `humanizer` no debe haber cambiado nada protegido.
6. **Genera:**
   ```bash
   uv run .claude/skills/rup-caso-de-uso/scripts/generar.py entrada.json
   ```
   El documento queda en `docs/UCS <Nombre>.docx`.
7. **Informa** de los avisos que queden y de los datos que confirmaste.

Si aún hay pendientes, genera un borrador y dilo con claridad:

```bash
uv run .claude/skills/rup-caso-de-uso/scripts/generar.py entrada.json --borrador
```

## Opciones

| Opción | Efecto |
|---|---|
| `--salida RUTA` | Escribe en otra ruta |
| `--borrador` | Admite pendientes y bloqueos del lint; no es una versión final |
| `--sobrescribir` | Reemplaza un archivo existente, que por defecto se protege |
| `--pdf` | Deja también una copia en PDF |
| `--solo-lint` | Revisa sin crear ningún documento |

Requiere `uv`, LibreOffice (`soffice`) y `pdftotext`. Las páginas del índice se calculan con LibreOffice: en Word pueden diferir, y se actualizan con F9.
