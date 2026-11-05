# Reglas de redacción: Especificación Suplementaria

Cómo se escribe cada sentencia. Los ID de fuente (F1, F2...) y su nivel de evidencia están en `../../_rup-comun/reglas-comunes.md`.

| ID | Se escribe así | Fuente |
|---|---|---|
| S1 | Contiene los requisitos que no pertenecen a un caso de uso: reportes, auditoría, seguridad, autenticación, cualidades y restricciones. | F4 |
| S2 | Cada requisito está identificado y etiquetado. | F4 |
| S3 | Una sentencia con uno de los patrones de S4. Un requisito por sentencia. | F13 |
| S5 | Desempeño: tiempos de respuesta concretos. | F4 |
| S6 | Confiabilidad: porcentaje de disponibilidad, MTBF y MTTR. | F4 |
| S7 | Si se usa un término como "crítico", se define. | F4 |
| S8 | Una restricción es una decisión obligatoria de diseño. | F4 |
| S9 | Lo que el sistema hace ante fallos se escribe. Es la omisión más común. | F13 |
| S10 | La medición se decide según el riesgo: un criterio verificable basta y no todo necesita cifra. | F14 |

### S4. Patrones EARS en español

| Tipo | Forma | Ejemplo |
|---|---|---|
| Siempre activo | `El Sistema deberá <respuesta>.` | El Sistema deberá registrar cada inicio de sesión. |
| Por evento | `Cuando <evento>, el Sistema deberá <respuesta>.` | Cuando se registre un pago, el Sistema deberá generar el recibo. |
| Por estado | `Mientras <estado>, el Sistema deberá <respuesta>.` | Mientras exista un cobro vencido, el Sistema deberá mostrar su estado. |
| No deseado | `Si <condición>, entonces el Sistema deberá <respuesta>.` | Si falla el envío del correo, entonces el Sistema deberá registrar el error. |
| Opcional | `Donde <característica>, el Sistema deberá <respuesta>.` | Donde exista firma electrónica, el Sistema deberá guardar la constancia. |

Los ejemplos muestran la forma y no son requisitos de SGP.
