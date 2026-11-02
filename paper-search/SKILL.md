---
name: paper-search
description: Busca papers y documentos científicos en fuentes oficiales (arXiv, Semantic Scholar, Europe PMC, OpenAlex), descarga el PDF legal y lo lee convirtiéndolo a texto. Use when the user wants scientific papers, investigación académica, estado del arte, revisión de literatura, evidence on a topic, or asks "busca papers/papers sobre X", even if they only mention a topic without the word "paper". Also use for finding the readable PDF of a paper with a known DOI.
---

# paper-search — buscar y leer papers científicos

Buscas en APIs oficiales (JSON), haces triage de candidatos y lees el PDF.
Nunca cite de memoria: todo claim debe venir del abstract o del PDF real.

## Herramienta central

Scripts (stdlib only, sin instalar nada):

```
python3 ~/.agents/skills/paper-search/scripts/papers.py search "QUERY" [--domain D] [--limit N] [--year YYYY-YYYY|YYYY:] [--sort relevance|citations|date] [--abstract]
python3 ~/.agents/skills/paper-search/scripts/papers.py read PDF_URL --pages 1-3 [--out notes.txt]
```

## 1. Clasificar el dominio del tema y elegir fuente

`--domain auto` (default) busca en Semantic Scholar (índice universal) con
fallback OpenAlex. Para temas de dominio claro, usa la fuente especialista:

| Dominio del tema | `--domain` | 1ª fuente (API) | Fallback |
|---|---|---|---|
| IA / ML / NLP / visión / robótica / CS | `ml` | arXiv | Semantic Scholar |
| Física / astronomía | `phys` | arXiv | Semantic Scholar |
| Matemáticas | `math` | arXiv | Semantic Scholar |
| Bio / genética / medicina / farmaco / COVID | `bio` | Europe PMC | Semantic Scholar |
| Psicología / ciencias cognitivas | `psy` | Europe PMC | Semantic Scholar |
| Química / materiales | `chem` | Semantic Scholar | OpenAlex |
| General / interdisciplinar | `auto` | Semantic Scholar | OpenAlex |

Notas de routing:
- Semantic Scholar es la mejor ley universal: devuelve abstract, `citationCount`
  y `openAccessPdf.url` en un solo hit. Empieza por ahí si dudas.
- "estado del arte / top papers del área" → `--sort citations`.
- "lo más reciente" → `--sort date` o `--year` reciente.
- Query SIEMPRE en inglés (las APIs están en inglés); traduce mentalmente el
  tema del usuario antes de buscar.

## 2. Triage (tú lo haces, no la script)

Presenta al usuario la lista con 3 categorías, bien con `--abstract` o tras
leer abstracts:
- **landmark**: muchas citas y viejo → fondo del campo.
- **reciente**: ≤ 2 años y relevante, citas aún pocas → frontera actual.
- **marginal**: tangencial → descartar, no presentarlo.

Muestra siempre: título, año, DOI, citas, URL del PDF. Nunca inventes citas.

## 3. Leer (abstract primero, PDF solo si hace falta)

1. El **abstract** de la búsqueda basta la mayoría de las veces — no descargues
   el PDF si el abstract responde la pregunta.
2. PDF necesario (método, resultados, figuras):
   ```
   papers.py read <pdf_url> --pages 1-3          # abstract+intro: suficiente casi siempre
   papers.py read <pdf_url> --pages 25-30        # conclusiones / discusión
   papers.py read <pdf_url> --out /tmp/opencode/paper.txt  # guardar para re-leer
   ```
3. Si la lectura falla con "not a PDF / paywall" → busca copia legal con el DOI:
   ```
   webfetch https://api.unpaywall.org/v2/<DOI>?email=unpaywall@ourresearch.org
   ```
   usa `best_oa_location.url_for_pdf`. Fuentes acreditadas de copias
   legales: repositorios del autor, Europe PMC, arXiv, CORE, DOAJ.
   Nunca githubs de shadow libraries ni sci-hub.

## 4. Síntesis citada (claim a claim)

- Cada claim cita su fuente: "(Vaswani et al. 2017, arXiv:1706.03762)".
- Si el usuario pidió "estado del arte" o "reporte": escribir los hallazgos en
  un Markdown en la carpeta de notas del repo (misma convención que la skill
  `research`); si no hay, `docs/notas/` y avisar dónde quedó.
- Paraayar lectura larga: delegate la lectura de muchos PDFs a un subagent
  `background` — perguntale que extraiga abstract + conclusions + 2-3
  claims citados por paper.

## 5. Reglas

- Máx 10 resultados por query; refina el query en vez de paginar.
- Rate limits: Semantic Scholar 1 req/seg — espera entre llamadas las que
  hagas seguidas; OpenAlex/Crossref piden `mailto` en la query (la script
  ya lo manda).
- Si ni Semantic Scholar ni la fuente del dominio dan el PDF, prueba
  manualmente Crossref (`api.crossref.org/works?query=`) o DOAJ
  (`doaj.org/api/search/articles/`) — una sola llamada webfetch basta.
- Solo fuentes oficiales; pdf_url que no sea del dominio oficial (arxiv.org,
  europepmc.org, doi.io OA, repositorio `.universidad.edu`) → validar con
  Unpaywall antes de leer.
