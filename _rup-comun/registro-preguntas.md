# Registro de preguntas y respuestas

Cada documento tiene un registro de lo que se preguntó al usuario. Evita inventar datos y repetir preguntas entre sesiones. Sin registro, `generar.py` no crea la versión final, solo un borrador.

## Dónde va

`preguntas-respuestas.md`, en la misma carpeta que el JSON del documento. Es un solo archivo para todos los documentos de esa carpeta, con una sección por documento. Otra ruta se indica con `--registro`.

## Formato

```markdown
# Preguntas y respuestas

## Generales

| N.º | Fecha | Pregunta | Respuesta |
|---|---|---|---|
| 1 | 05/Noviembre/2026 | ¿Cuál es el nombre oficial del sistema? | Gestión de Inmuebles |

## UCS Solicitar cita

| N.º | Fecha | Pregunta | Respuesta |
|---|---|---|---|
| 1 | 05/Noviembre/2026 | ¿Quién cancela una cita? | el administrador |

## Glosario

Sin preguntas: todos los datos salieron de los documentos del proyecto.
```

El título de cada sección es el del documento: `UCS <Nombre>`, `Especificación Suplementaria` o `Glosario`. `## Generales` guarda lo que vale para varios documentos.

## Reglas

1. **Léelo antes de redactar.** Lee `## Generales` y la sección del documento. Si el archivo no existe, créalo.
2. **Guarda al recibir.** Anota cada respuesta en cuanto llega, sin esperar al final, para no perderla si termina la sesión.
3. **Copia la respuesta textual.** No la resumas ni corrijas su ortografía. Una interpretación tuya va aparte y marcada como tal.
4. **No preguntes dos veces.** Si la respuesta ya está, úsala.
5. **Nunca borres una respuesta.** Si el usuario cambia de opinión, agrega una fila nueva: vale la más reciente.
6. **Prioridad de fuentes:** respuesta del usuario, documentos del proyecto, diagramas.
7. **Sin preguntas también se anota.** Si no hizo falta preguntar nada, escribe `Sin preguntas:` y de dónde salieron los datos.

## Datos de cada edición

Antes de generar, presenta una sugerencia para cada dato, pide confirmarla o cambiarla y anota la respuesta en la sección del documento:

| Dato | Sugerencia |
|---|---|
| Fecha | La fecha de hoy, con la forma dd/Mes/aaaa |
| Versión | La última del historial más 0.1, o 1.0 si el documento es nuevo |
| Descripción | Una frase con lo que cambió en esta edición |
| Autor | El autor que el usuario indicó en el registro o, si no hay, el de la última revisión |

Con los cuatro confirmados, añade la revisión al `historial` y pon `redaccion.revision_confirmada: true`. Sin esa marca, `generar.py` no crea la versión final. La marca declara que preguntaste: no la pongas si no lo hiciste.

## Límite

El script comprueba que el registro y la sección existan y que tengan contenido. No comprueba que cada dato del documento salga de ahí. Eso depende de seguir la regla "Nada se inventa".
