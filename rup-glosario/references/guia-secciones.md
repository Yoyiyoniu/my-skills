# Guía por secciones: Glosario

Hay un solo glosario para el sistema. Define los términos del dominio que un lector de los casos de uso podría no conocer. La forma de cada definición está en `reglas-redaccion.md`.

| Sección | Campo | Contenido |
|---|---|---|
| 1.1 Propósito | `introduccion.proposito` | Para qué sirve este glosario. |
| 1.2 Alcance | `introduccion.alcance` | Proyecto y documentos a los que aplica. |
| 1.3 Referencias | `introduccion.referencias` | Documentos citados. |
| 1.4 Descripción general | `introduccion.descripcion_general` | Cómo está organizado. |
| 2. Definiciones | `terminos`, `grupos` | Términos en orden alfabético y grupos por subdominio. |
| 3. Estereotipos UML | `estereotipos` | Estereotipos propios y su significado. La sección se conserva aunque no haya ninguno. |

## Contrato del JSON

`assets/ejemplo.json` es el modelo completo.

- Término: `{ "termino", "definicion" }`.
- Grupo: `{ "nombre", "descripcion", "terminos": [...] }`. Agrupa solo si mezclar subdominios confundiría al lector.
- Estereotipo: `{ "nombre", "significado" }`.

El orden del JSON no importa: el generador ordena los términos. Primero van los sueltos y después los grupos, como en la plantilla.

## Extraer candidatos

1. Convierte los UCS a texto como indica `SKILL.md`.
2. Lista actores, objetos del negocio, estados y términos que aparezcan en varios UCS.
3. Agrupa las variantes de un mismo concepto y elige un nombre. Si los documentos se contradicen, pregunta.
4. Presenta la lista al usuario antes de redactar definiciones.

## Comprobaciones antes de entregar

- ¿Cada definición sale de un documento del proyecto o del usuario? Si no, es `[PENDIENTE: definición de <término>]`.
- ¿Algún par de términos se define entre sí?
