# Reglas de redacción: Caso de uso

Cómo se escribe cada sentencia. Los ID de fuente (F1, F2...) y su nivel de evidencia están en `../../_rup-comun/reglas-comunes.md`.

### Forma de cada sentencia

| ID | Se escribe así | Ejemplo | Fuente |
|---|---|---|---|
| U1 | **Nombre:** verbo en infinitivo + objeto, desde la perspectiva del actor que lo inicia. | Solicitar cita | F3 |
| U2 | **Inicio:** `Este caso de uso comienza cuando <actor> <acción>.` Un solo actor inicia. | Este caso de uso comienza cuando el Cliente potencial solicita una cita para un inmueble. | F1, F2, F3 |
| U3 | **Paso:** `<Actor o El Sistema> <verbo en presente activo> <objeto>.` Un paso, una acción. | El Sistema registra la solicitud de cita. | F7, F8, F3 |
| U4 | **Los tres tipos de paso:** pasar información, validar una condición o actualizar estado. | El Cliente potencial proporciona su nombre, correo y teléfono. | F6 |
| U5 | **Validar:** `El Sistema valida <dato o regla>.` El fallo va en un flujo alterno. | El Sistema valida los datos obligatorios. | F6 (título "Validate, Don't Check Whether") |
| U6 | **Intención del actor**, no los movimientos en la interfaz. | El Cliente potencial envía la solicitud. | F6 |
| U7 | **Datos:** nombrar lo que se intercambia. Si la lista es larga, un nombre definido en el Glosario. | Datos de contacto (definido en el Glosario) | F1, F2, F6 |
| U8 | **Qué, no cómo:** nada de la solución interna. | El Sistema registra el pago. | F1, F8 |
| U9 | **Actor:** nombre del rol completo y siempre igual. | Cliente potencial | F3 |
| U10 | **Largo:** entre 3 y 9 pasos en el flujo básico. | | F6 |
| U11 | **Final:** el último paso indica cómo termina. | El caso de uso finaliza. | F1 |

### Flujos alternos

| ID | Se escribe así | Fuente |
|---|---|---|
| U12 | Primera línea: `Este flujo comienza en el paso <N> del flujo básico cuando <condición>.` | F2, F3 |
| U13 | Última línea: `El flujo regresa al paso <N>.` o `El caso de uso finaliza.` Un solo desenlace. | F2, F3, F6 |
| U14 | La condición describe algo que el Sistema puede detectar. | F6 |
| U15 | Las alternativas salen del flujo básico: separadas, viables y con numeración coherente. | F7, F8 |
| U16 | La negación se reserva para flujos alternos y de excepción. | F9 |

### Condiciones y extensión

| ID | Se escribe así | Fuente |
|---|---|---|
| U17 | **Precondición:** estado del sistema necesario para empezar, en presente. `Existe un inmueble publicado.` | F1, F2 |
| U18 | **Postcondición:** estado posible al terminar. `La solicitud de cita queda registrada.` | F1, F2 |
| U19 | Las condiciones no encadenan casos de uso. | F1 |
| U20 | **Requerimiento especial:** no funcional y propio de este caso de uso. | F1, F2 |
| U21 | **Punto de extensión:** nombre y ubicación en el flujo. | F1, F2 |
