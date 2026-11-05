# Reglas comunes de redacción

Fuentes, reglas y decisiones que valen para los tres documentos. Las formas en español son una adaptación de este proyecto: las fuentes están en inglés.

## Fuentes

Evidencia: **A** = se leyó el texto original. **B** = se conoce por otra fuente que lo cita o por un fragmento. **C** = solo índice o catálogo.

| ID | Fuente | Evidencia |
|---|---|---|
| F1 | IBM Rational, *RUP: Detail a Use Case*. [Copia](https://cin.ufpe.br/~if682/RUP/process/activity/ac_desuc.htm) | A |
| F2 | IBM Rational, *RUP: plantilla Use-Case Specification*. [Copia](https://files.defcon.no/RUP/webtmpl/templates/req/rup_ucspec.htm) | A |
| F3 | IBM Rational, *RUP: Example Use-Case Modeling Guidelines*. [Copia](https://files.defcon.no/RUP/manuals/ucmgl/ucmgl.htm) | A, es un ejemplo y no norma de RUP |
| F4 | IBM Rational, *RUP: Develop Supplementary Specifications*. [Copia](https://home.iscte-iul.pt/~hro/RUPSmallProjects/core.base_rup/tasks/develop_supplementary_specification_52FC4CAE.html) | A |
| F5 | IBM Rational, *RUP: Artifact Glossary*. [Copia](https://files.defcon.no/RUP/process/artifact/ar_gloss.htm) | A |
| F6 | A. Cockburn, *Writing Effective Use Cases*, Addison-Wesley, 2001. [Extracto del borrador #3](https://courses.cs.duke.edu/compsci308/spring23/readings/cockburn_use_cases.pdf) | A en el extracto (recordatorios y proceso); C en los títulos del cap. 7 |
| F7 | K. Phalp, J. Vincent, K. Cox, "Improving the quality of use case descriptions: empirical assessment of writing guidelines", *Software Quality Journal*, 2007. [DOI](https://doi.org/10.1007/s11219-007-9023-6) | B, por F8 |
| F8 | J. Frattini, A. Frattini, "Adopting Use Case Descriptions for Requirements Specification: an Industrial Case Study", 2025. [arXiv](https://arxiv.org/abs/2506.13303) | A |
| F9 | K. Cox, K. Phalp, M. Shepperd, "Comparing Use Case Writing Guidelines", REFSQ, 2001. [PDF](https://scitech.bournemouth.ac.uk/staff/kphalp/refsq01.pdf) | B, servidor inaccesible |
| F10 | C. Ben Achour, C. Rolland, N. Maiden, C. Souveyet, "Guiding Use Case Authoring: Results of an Empirical Study", IEEE RE, 1999 | B |
| F11 | H. Femmer, D. Méndez Fernández, S. Wagner, S. Eder, "Rapid Quality Assurance with Requirements Smells", *Journal of Systems and Software*, 2017. [arXiv](https://arxiv.org/abs/1611.08847) | A |
| F12 | ISO/IEC/IEEE 29148, criterios de lenguaje | B, por F11; la norma es de pago |
| F13 | A. Mavin, P. Wilkinson, A. Harwood, M. Novak, "Easy Approach to Requirements Syntax (EARS)", IEEE RE, 2009. [DOI](https://doi.org/10.1109/RE.2009.9) | A |
| F14 | M. Glinz, "On Non-Functional Requirements", IEEE RE, 2007. [PDF](https://files.ifi.uzh.ch/rerg/amadeus/publications/papers/RE07_Glinz.pdf) | B |
| F15 | R. Wehbe, "The Language Extended Lexicon, Revisited", 2011, sobre el LEL de J. C. S. P. Leite. [PDF](https://40jaiio.sadio.org.ar/sites/default/files/T2011/ASSE/753.pdf) | A |
| F16 | ISO 704:2022, *Terminology work: Principles and methods*. [Catálogo](https://standards.iteh.ai/catalog/standards/iso/041b1c72-c51f-4947-a66b-c7b7f10c185d/iso-704-2022) | C |
| F17 | RAE, *Diccionario panhispánico de dudas*, entrada "deber". [DPD](https://www.rae.es/dpd/deber) | B, fragmento y fuentes que lo citan |

## Reglas comunes

| ID | Se escribe así | Fuente |
|---|---|---|
| C1 | Frases cortas y vocabulario simple: un término sencillo antes que uno complejo. | F1 |
| C2 | Un mismo concepto se nombra siempre igual. Sin sinónimos para variar. | F3, F7 |
| C3 | Obligación con `deber` + infinitivo o `deberá`, sin "de". "Debe de" expresa suposición. | F17 |
| C4 | Un dato desconocido se marca como pendiente. No se rellena. | F3 ("TBD"), adaptado a `[PENDIENTE: ...]` |
| C5 | Toda referencia debe poder seguirse: título, número o nombre exacto. | F11 |

## Conflictos entre fuentes

| Conflicto | Decisión |
|---|---|
| F3 pide futuro ("The system will"). F7 pide presente simple y voz activa. | Presente en los pasos: F3 es un ejemplo y F7 tiene respaldo empírico. `deberá` queda para requisitos. |
| F6 pide solo el apodo del dato. F1 y F2 piden ser explícitos. | Se manda F1: nombrar los datos. Una lista larga pasa al Glosario (U7). |
| F7 pide evitar adverbios y adjetivos. F8 descartó esa regla en su estudio. | Se bloquean adverbios de relleno y no todos los adjetivos. |
| `humanizer` pide variar frases. U3 pide una forma fija. | En pasos manda U3. `humanizer` trabaja la prosa. |
| F4 pide cifras. F14 decide según el riesgo. | Criterio verificable o `[PENDIENTE: ...]`, sin exigir siempre cifra. |

La evidencia empírica es limitada: F8 señala que hay poca sobre criterios de calidad de casos de uso, y un resultado suyo fue contrario a la guía. Estas reglas son buena práctica documentada, no garantía de calidad. Los detectores tampoco son exactos: F11 trata cada hallazgo como una señal a revisar.

## Lo que no se pudo verificar

- **F9 y F7:** el servidor de Bournemouth rechazó la conexión y Springer redirigió a inicio de sesión. Sus reglas vienen de F8 y de resúmenes.
- **Cockburn, capítulo 7:** solo se confirmaron títulos. El texto de la regla de validar es interpretación de ese título.
- **ISO 29148 e ISO 704:** de pago. No se citan literalmente.
- **Durán et al., WER 1999 (patrones lingüísticos):** existe, pero no se pudo leer. Sería la mejor fuente para la forma en español y sigue pendiente.
- **Adolph y Bramble; Lilly:** no se encontraron. No se usan.
