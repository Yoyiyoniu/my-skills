---
name: rup-especificacion-suplementaria
description: Redacta y genera la Especificación Suplementaria (o complementaria) en .docx sobre la plantilla RUP del proyecto, con requisitos en patrones EARS, criterios verificables, negative prompt, lint en español y paso obligatorio por humanizer. Usar cuando el usuario pida crear o redactar la especificación suplementaria o complementaria, o documentar en ese formato requisitos no funcionales, usabilidad, confiabilidad, desempeño, soporte, restricciones de diseño o interfaces.
---

# Especificación Suplementaria

Produce el documento de 13 secciones que recoge lo que no pertenece a un solo caso de uso.

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

1. **Reúne los requisitos.** Lee los UCS de `docs/` para no duplicar lo que ya cubren. En Funcionalidad van solo requisitos transversales; cita los casos de uso por su nombre y no copies sus flujos. Pregunta cada umbral: no propongas cifras por tu cuenta.
2. **Redacta el JSON** en un archivo fuera de `docs/`, con `assets/ejemplo.json` como modelo.
3. **Revisa** desde la raíz del repositorio:
   ```bash
   uv run .claude/skills/rup-especificacion-suplementaria/scripts/generar.py entrada.json --solo-lint
   ```
   Corrige los bloqueos y revisa cada aviso.
4. **Invoca la skill `humanizer`** como indica `redaccion-humanizada.md`. Después pon `redaccion.humanizer_aplicado: true`.
5. **Vuelve a revisar** con `--solo-lint`: `humanizer` no debe haber cambiado nada protegido.
6. **Genera:**
   ```bash
   uv run .claude/skills/rup-especificacion-suplementaria/scripts/generar.py entrada.json
   ```
   El documento queda en `docs/Especificacion Suplementaria.docx`.
7. **Informa** de los avisos que queden y de los datos que confirmaste. Recuerda que el índice se actualiza con F9 si el equipo abre el documento en Word.

Si aún hay pendientes, genera un borrador y dilo con claridad:

```bash
uv run .claude/skills/rup-especificacion-suplementaria/scripts/generar.py entrada.json --borrador
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
