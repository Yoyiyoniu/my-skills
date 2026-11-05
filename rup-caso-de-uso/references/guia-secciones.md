# Guía por secciones: Caso de uso

Qué va en cada sección, según la plantilla RUP, y qué campo del JSON la llena. La forma de cada sentencia está en `reglas-redaccion.md`.

| Sección | Campo | Contenido |
|---|---|---|
| 1. Nombre | `contenido.nombre` | Verbo en infinitivo y objeto, desde la perspectiva del actor que lo inicia. |
| 1.1 Breve descripción | `descripcion` | El papel y propósito del caso de uso en un párrafo. |
| 2.1 Flujo básico | `inicio`, `flujo_basico` | Qué hace el actor para iniciar y el diálogo entre actor y Sistema. Describe qué ocurre, no cómo ni por qué. |
| 2.2 Flujos alternos | `flujos_alternos` | Excepciones y variantes. Cada uno dice dónde comienza y cómo termina. |
| 3. Requerimientos especiales | `requerimientos_especiales` | Requisitos no funcionales propios de este caso de uso. Los transversales van en la Especificación Suplementaria. |
| 4. Precondiciones | `precondiciones` | Estado necesario para empezar. |
| 5. Postcondiciones | `postcondiciones` | Estados posibles al terminar. |
| 6. Puntos de extensión | `puntos_extension` | Nombre y paso del flujo donde se ubica. |

## Contrato del JSON

`assets/ejemplo.json` es el modelo completo. Campos que conviene mirar:

- `actores`: lista de nombres exactos. El lint exige que cada paso empiece por uno de ellos o por "El Sistema".
- `actor_principal`: debe estar en `actores` y aparecer en `inicio`.
- `inicio`: continúa la frase "Este caso de uso comienza cuando ...".
- `flujo_basico`: objetos `{ "paso": "...", "subpasos": ["..."] }`. El cierre "El caso de uso finaliza." se añade solo.
- Flujo alterno: `nombre`, `desde_paso`, `condicion`, `pasos` y un único desenlace, `regresa_a_paso` o `finaliza: true`. `subflujos` es opcional, con la misma forma.
- `condicion`: continúa la frase "Este flujo comienza en el paso N del flujo básico cuando ...".
- `requerimientos_especiales`, `precondiciones`, `postcondiciones`: objetos `{ "nombre", "descripcion" }`. `nombre` es el título corto que aparece en el índice.
- `puntos_extension`: objetos `{ "nombre", "paso", "descripcion" }`.

Las listas pueden ir vacías: el documento conserva la sección con una frase fija.

## Comprobaciones antes de entregar

- ¿Cada alternativa está fuera del flujo básico?
- ¿Se nombran los datos que se intercambian?
- ¿Los términos de negocio están en el Glosario? La skill no lo comprueba: revísalo a mano.
