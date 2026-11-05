# Guía por secciones: Especificación Suplementaria

Recoge lo que no pertenece a un solo caso de uso: requisitos transversales, cualidades y restricciones. Lo propio de un caso de uso va en ese caso de uso. La forma de cada sentencia está en `reglas-redaccion.md`.

| Sección | Campo | Contenido |
|---|---|---|
| 1. Introducción | `introduccion` | Objetivo, alcance, definiciones, referencias y descripción general del documento. |
| 2. Funcionalidad | `funcionalidad` | Funciones transversales: reportes, auditoría, impresión, seguridad, autenticación. |
| 3. Usabilidad | `usabilidad` | Tiempo de capacitación, tiempos de tarea medibles, estándares de interfaz. |
| 4. Confiabilidad | `confiabilidad` | Disponibilidad en porcentaje, MTBF, MTTR, precisión. |
| 5. Desempeño | `desempeno` | Tiempo de respuesta, rendimiento, capacidad, modos de degradación, uso de recursos. Cita los casos de uso por su nombre. |
| 6. Soporte | `soporte` | Mantenimiento, convenciones, utilidades de soporte. |
| 7. Restricciones de diseño | `restricciones_diseno` | Decisiones obligatorias: lenguajes, herramientas, arquitectura. |
| 8. Documentación y ayuda | `documentacion` | Ayuda en línea y documentación de usuario. |
| 9. Componentes adquiridos | `componentes_adquiridos` | Componentes de terceros y sus restricciones. |
| 10. Interfaces | `interfaces` | Usuario, hardware, software y comunicación. Las cuatro subsecciones se conservan siempre. |
| 11. Licencia | `licencia` | Requisitos de licencia y restricciones de uso. |
| 12. Avisos legales | `avisos_legales` | Exenciones, garantías, derechos de autor, marcas. |
| 13. Normas aplicables | `normas` | Normas y secciones concretas que aplican. |

## Contrato del JSON

`assets/ejemplo.json` es el modelo completo.

- Secciones 2 a 7: `{ "requisitos": [...] }` o `{ "no_aplica": true }`.
- Requisito: `{ "titulo", "descripcion", "casos_uso": [...] }`. `casos_uso` es opcional.
- Secciones 8, 9, 11, 12, 13 y cada interfaz: `{ "texto": ["párrafo"] }` o `{ "no_aplica": true }`.
- `introduccion.definiciones`: `{ "remite_glosario": true }` o `{ "texto": "..." }`.

Una sección omitida es un error: si no aplica, hay que declararlo.

## Comprobaciones antes de entregar

- ¿Algún requisito repite un flujo de un caso de uso? Remite a él por su nombre.
- ¿Cada operación que puede fallar tiene su requisito con el patrón "Si ..., entonces"?
- ¿Cada umbral lo dio el usuario? Si no, debe ser `[PENDIENTE: ...]`.
