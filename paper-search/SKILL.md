---
name: paper-search
description: >-
  Searches official scholarly APIs (arXiv, Semantic Scholar, Europe PMC,
  OpenAlex), reads the legal PDF, and writes a cited note from those papers.
  Use when the user wants scientific papers, a literature review, state of
  the art, evidence on a topic, a known DOI, or says "busca papers sobre X",
  even if they never use the word paper.
---

# paper-search

Search official APIs and read the legal PDF. A scientific claim is allowed only when the abstract or the PDF pages read in this session contain it. Do not supply it from memory, a blog, or any other secondary write-up. Follow every claim back to the paper that owns it.

Year, DOI, and citation count come from the script output. If `citations=-`, the source did not provide a count. Say that. Do not estimate it.

## Delegate the reading

For a literature review, a state of the art, or any report that needs more than one paper, spin up a background agent to do the reading so this conversation can keep going. A single paper or a known DOI stays here.

The background agent's job:

1. Investigate the question against the papers themselves, not a secondary write-up of them.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes. Match the existing convention. If there is none, write `docs/notes/<topic>.md` and say where.

Give it the absolute path to `scripts/papers.py`, the question, the domain, and the output path. It uses the script below and does not reimplement the APIs.

## Script

`scripts/papers.py` sits next to this file. Stdlib only. Run it by absolute path.

```bash
python3 scripts/papers.py search "QUERY" [--domain auto|ml|phys|math|bio|psy|chem] [--limit N] [--year 2020|2020-2024|2020-] [--sort relevance|citations|date] [--abstract]
python3 scripts/papers.py read PDF_URL --pages 1-3 [--out notes.txt]
python3 scripts/papers.py oa 10.xxxx/yyyy
```

`oa` prints `is_oa=` and `pdf=` from Unpaywall. One query, `--limit` at most 10. If the hit list is wrong, change the query. Do not page.

Optional: `SEMANTIC_SCHOLAR_API_KEY` (fewer 429s) and `PAPER_SEARCH_EMAIL` (OpenAlex and Unpaywall).

## Routing

Translate the query to English before searching.

| Topic | `--domain` | First source | If it fails |
|---|---|---|---|
| AI / ML / NLP / vision / robotics / CS | `ml` | arXiv | Semantic Scholar, then OpenAlex |
| Physics / astronomy | `phys` | arXiv | Semantic Scholar, then OpenAlex |
| Mathematics | `math` | arXiv | Semantic Scholar, then OpenAlex |
| Bio / medicine / genetics / pharma | `bio` | Europe PMC | Semantic Scholar, then OpenAlex |
| Psychology / cognitive science | `psy` | Europe PMC | Semantic Scholar, then OpenAlex |
| Chemistry / materials | `chem` | Semantic Scholar | OpenAlex |
| Mixed or unclear | `auto` | Semantic Scholar | OpenAlex |

- State of the art, or "most cited": `--sort citations`. arXiv has no citation counts, so that sort starts at Semantic Scholar.
- What is new: `--sort date` or `--year 2023-`.
- A paper named by its title: search that English title. With `--sort relevance`, an identical title is ranked first.

## Triage

Run the search with `--abstract`. Keep only the papers you will use.

- **landmark**: heavily cited and older than two years.
- **recent**: from the last two years and on the question, even with few citations.
- **marginal**: off to the side. Leave it out of the note.

## Read

1. The abstract is enough unless the user asked for a method, a number, or a quotation.
2. Open the PDF only then: `read URL --pages 1-3`. For the ending, read the last 2–4 pages. If you do not know the length, stay on 1–3. Do not guess page numbers.
3. `ERROR: not a PDF` or `pdf=(no open PDF…)`: run `oa <DOI>` and read the `pdf=` it prints. If `pdf=-`, there is no legal direct PDF. Keep the abstract. Do not treat the landing `url=` as the paper.
4. These hosts can be read directly: `arxiv.org`, `europepmc.org`, `ncbi.nlm.nih.gov`, and a university repository. Any other host goes through `oa` first.
5. Do not use Sci-Hub, Library Genesis, or other shadow-library mirrors.

Read at most three PDFs per run. If the question needs more, finish from abstracts and list the ones you did not open.

## Note

```markdown
# <question>

## Findings
- Claim, only if the abstract or the named pages say it. (Vaswani et al. 2017, 10.48550/arXiv.1706.03762, abstract)

## Papers
- **Attention Is All You Need** (2017) — 120404 citations, OpenAlex
  - doi: 10.48550/arXiv.1706.03762
  - pdf: https://arxiv.org/pdf/1706.03762
  - read: abstract only
  - why it is here: one line taken from that text

## Not read
- Papers left out as off-topic, or PDFs that were not opened.
```

In chat, point at the file. Do not paste it back. Same citation rule for a one-paper answer that never becomes a file: author, year, DOI, and whether it came from the abstract or from which pages.
