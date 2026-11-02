#!/usr/bin/env python3
"""papers.py — search scientific papers on official APIs and read their PDFs.

Subcommands:
  search QUERY [--domain auto|ml|phys|math|bio|psy|chem|general] [--limit N]
               [--year 2020-2023|2020:] [--sort relevance|citations|date]
               [--abstract]
  read PDF_URL_OR_PATH [--pages 1-3] [--out FILE]
  selftest

Stdlib only. PDF text extraction: pdftotext (poppler), pymupdf as lazy fallback.
"""
import argparse
import json
import re
import ssl
import subprocess
import sys
import urllib.parse
import urllib.request
import time
from xml.etree import ElementTree

UA = "paper-search-skill/1.0 (personal research tool)"
SSL_CTX = ssl.create_default_context()
TIMEOUT = 30


def http_json(url, retries=3):
    """GET url -> parsed JSON, retrying 429/5xx with linear backoff (S2 rate-limits)."""
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT, context=SSL_CTX) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500:
                raise
            last = e
        except urllib.error.URLError as e:  # timeouts count as retryable
            last = e
        if attempt + 1 < retries:
            time.sleep(2 * (attempt + 1))  # 2s, 4s, 6s
    raise last


def http_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=SSL_CTX) as r:
        return r.read().decode()


def get_json(base_url, params):
    return http_json(base_url + "?" + urllib.parse.urlencode(params))


# ---------------------------------------------------------------- arXiv ----
NS = {"a": "http://www.w3.org/2005/Atom"}


def arxiv_date(date):  # "2020" / "2020-01" -> arXiv submittedDate filter half
    y = int(date[:4])
    m = int(date[5:7]) if len(date) >= 7 else 1
    return f"{y:04d}{m:02d}010000"


def search_arxiv(query, limit, year, sort):
    sq = 'all:"{}"'.format(query) if " " in query else f"all:{query}"
    if year:
        parts = year.split(":")
        lo = arxiv_date(parts[0])
        hi = arxiv_date(parts[1]) if len(parts) > 1 and parts[1] else "999912312359"
        sq += f" AND submittedDate:[{lo} TO {hi}]"
    params = {"search_query": sq, "start": 0, "max_results": limit,
              "sortBy": {"relevance": "relevance", "date": "submittedDate"}[sort]}
    xml = http_text("https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params))
    root = ElementTree.fromstring(xml)
    out = []
    for e in root.findall("a:entry", NS):
        arxiv_id = e.find("a:id", NS).text.rsplit("/", 1)[-1]
        doi_el = e.find("a:doi", NS)
        out.append({
            "title": " ".join(e.find("a:title", NS).text.split()),
            "year": e.find("a:published", NS).text[:4],
            "doi": doi_el.text if doi_el is not None else "",
            "citations": "",
            "pdf": f"https://arxiv.org/pdf/{arxiv_id}",
            "abstract": " ".join(e.find("a:summary", NS).text.split()),
            "source": "arXiv",
        })
    return out


# ------------------------------------------------------ Semantic Scholar ---
def search_s2(query, limit, year, sort):
    params = {
        "query": query, "limit": min(limit, 100),
        "fields": "title,abstract,year,externalIds,citationCount,openAccessPdf,venue",
        "sort": {"citations": "citationCount:desc"}.get(sort, "relevance:desc"),
    }
    if year:
        params["year"] = year  # "2020-2023" or "2020-" both valid for the API
    data = get_json("https://api.semanticscholar.org/graph/v1/paper/search", params)
    out = []
    for p in data.get("data") or []:
        out.append({
            "title": p.get("title") or "",
            "year": p.get("year") or "",
            "doi": (p.get("externalIds") or {}).get("DOI", ""),
            "citations": p.get("citationCount") or 0,
            "pdf": ((p.get("openAccessPdf") or {}).get("url") or ""),
            "abstract": re.sub(r"\s+", " ", p.get("abstract") or ""),
            "source": "SemanticScholar",
        })
    return out


# ------------------------------------------------------------ OpenAlex ----
def openalex_abstract(inv):
    if not inv:
        return ""
    words = {}
    for w, positions in inv.items():
        for pos in positions:
            words[pos] = w
    return " ".join(words[i] for i in sorted(words))


def search_openalex(query, limit, year, sort):
    params = {"search": query, "per_page": min(limit, 100),
              "mailto": "papers-search@example.org"}
    filters = []
    if year:
        lo, _, hi = year.partition(":")
        if lo:
            filters.append(f"from_publication_date:{lo}-01-01")
        if hi:
            filters.append(f"to_publication_date:{hi}-12-31")
    params["sort"] = {"citations": "cited_by_count:desc", "date": "publication_date:desc"}.get(
        sort, "relevance_score:desc")
    if filters:
        params["filter"] = ",".join(filters) + ("," + params["sort"] if
                                                sort in ("citations",) else "")
    data = get_json("https://api.openalex.org/works", params)
    out = []
    for w in data.get("results") or []:
        loc = w.get("primary_location") or {}
        out.append({
            "title": re.sub(r"\s+", " ", w.get("display_name") or ""),
            "year": w.get("publication_year") or "",
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
            "citations": w.get("cited_by_count") or 0,
            "pdf": loc.get("pdf_url") or "",
            "abstract": openalex_abstract(w.get("abstract_inverted_index")),
            "source": "OpenAlex",
        })
    if sort == "citations":
        out.sort(key=lambda r: -(r["citations"] or 0))
    return out


# ----------------------------------------------------------- Europe PMC ---
def search_europepmc(query, limit, year, sort):
    q = f"({query})"
    if year:
        lo, _, hi = year.partition(":")
        if hi:
            q += f' AND (PUB_YEAR:[{lo} TO {hi}])'
        else:
            q += f" AND (PUB_YEAR:{lo})"
    params = {"query": q, "format": "json", "resultType": "core",
              "pageSize": min(limit, 100)}
    sort_map = {"citations": "CITED", "date": "DATE"}
    if sort in sort_map:
        params["sort"] = sort_map[sort]
    data = get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search", params)
    out = []
    for hit in data.get("resultList", {}).get("result", []):
        pdf_link = ""
        for u in hit.get("fullTextUrlList", {}).get("fullTextUrl", []):
            if u.get("documentStyle") == "pdf":
                pdf_link = u.get("url", "")
                break
        if pdf_link.startswith("http://europepmc.org"):
            pdf_link = pdf_link.replace("http://", "https://")
        out.append({
            "title": re.sub(r"\s+", " ", hit.get("title", "")),
            "year": hit.get("pubYear", ""),
            "doi": hit.get("doi", ""),
            "citations": hit.get("citedByCount", 0) or 0,
            "pdf": pdf_link,
            "abstract": re.sub(r"\s+", " ", hit.get("abstractText", "")),
            "source": "EuropePMC",
        })
    return out


DOMAIN_SOURCES = {
    "ml": (search_arxiv, search_s2),
    "phys": (search_arxiv, search_s2),
    "math": (search_arxiv, search_s2),
    "bio": (search_europepmc, search_s2),
    "psy": (search_europepmc, search_s2),
    "chem": (search_s2, search_openalex),
    "general": (search_s2, search_openalex),
    "auto": (search_s2, search_openalex),
}


def do_search(query, domain, limit, year, sort, show_abstract):
    results, err = [], None
    # universal safety net: OpenAlex indexes ~250M works and is the most reliable API
    for fn in [*DOMAIN_SOURCES[domain], search_openalex]:
        if results:  # first successful source wins; don't call lower-priority ones
            break
        if fn is search_openalex and search_openalex in DOMAIN_SOURCES[domain]:
            continue  # already in chain (general/chem) — don't call twice
        try:
            results = fn(query, limit, year, sort)
        except Exception as e:  # network / rate limit / parse: try next source
            err = (err + "; " if err else "") + f"{fn.__name__}: {e}"
    if not results:
        print(f"ERROR: all sources failed — {err}", file=sys.stderr)
        return 1
    if err:
        print(f"NOTE: fallback used ({err})", file=sys.stderr)
    print_results(results, show_abstract)
    return 0


def print_results(results, show_abstract):
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}  [{r['source']}]")
        print(f"   year={r['year']}  doi={r['doi'] or '-'}  citations={r['citations'] or '-'}")
        print(f"   pdf={r['pdf'] or '(paywall — try Unpaywall with the DOI)'}")
        if show_abstract:
            print(f"   abstract: {r['abstract'][:600]}{'…' if len(r['abstract']) > 600 else ''}")


# ---------------------------------------------------------------- read ----
def download_pdf(url, path):
    subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "90", url, "-o", path],
                   check=True)


def do_read(target, pages, out_file):
    path = target
    if re.match(r"^https?://", target):
        path = "/tmp/opencode/paper-search.pdf"
        download_pdf(target, path)
    lo, _, hi = (pages or "").partition("-")
    start, end = (int(lo), int(hi or lo)) if pages else (None, None)
    cmd = ["pdftotext"]
    if pages:
        cmd += ["-f", lo, "-l", hi or lo]
    cmd += [path, "-"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
    except FileNotFoundError:
        pass  # poppler not installed -> pymupdf fallback
    try:
        import pymupdf
    except ImportError:
        raise SystemExit("ERROR: neither pdftotext nor pymupdf available; "
                         "run: pip install pymupdf")
    doc = pymupdf.open(path)
    rng = range(start - 1, end) if pages else range(doc.page_count)
    return "".join(doc[i].get_text() for i in rng if i < doc.page_count)


def do_read(target, pages, out_file):
    path = target
    if re.match(r"^https?://", target):
        path = "/tmp/opencode/paper-search.pdf"
        subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "90",
                        target, "-o", path], check=True)
    with open(path, "rb") as f:
        if not f.read(5).startswith(b"%PDF"):
            raise SystemExit(
                f"ERROR: not a PDF ({target}). Probably a paywall landing page. "
                "Use the DOI with Unpaywall: https://api.unpaywall.org/v2/<DOI>?email=you@example.org")
    text = extract_pdf_text(path, pages)
    if not text.strip():
        raise SystemExit("ERROR: PDF downloaded but no text extracted "
                         "(scanned pages? try pymupdf or download elsewhere)")
    if out_file:
        with open(out_file, "w") as f:
            f.write(text)
        print(f"saved {len(text)} chars to {out_file}")
    else:
        print(text)
    return 0


# -------------------------------------------------------------- selftest --
def selftest():
    print("== search arXiv (ml) ==")
    results, err = [], None
    try:
        results = search_arxiv("attention is all you need", 5, None, "relevance")
    except Exception as e:
        err = e
    assert results, f"arxiv search failed: {err}"
    assert any("Attention" in r["title"] for r in results), "expected the transformer paper"
    print(f"OK: {len(results)} results, top: {results[0]['title']}")

    print("== search general (SemanticScholar w/ OpenAlex fallback) ==")
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = do_search("CRISPR base editing", "general", 5, None, "relevance", False)
    assert rc == 0, "general search failed on all sources"
    lines = buf.getvalue()
    assert "CRISPR" in lines, f"unexpected results:\n{lines}"
    src = [l for l in lines.splitlines() if "CRISPR" in l][0]
    print(f"OK via {('OpenAlex' if 'OpenAlex' in src else 'SemanticScholar')}: {src.strip()[:90]}")

    print("== read first arXiv PDF page 1 ==")
    arxiv_pdf = next(r["pdf"] for r in results if r["pdf"])
    path = "/tmp/opencode/paper-search-selftest.pdf"
    subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "90", arxiv_pdf, "-o", path], check=True)
    text = extract_pdf_text(path, "1")
    assert text.strip(), "no text extracted from arxiv pdf"
    print(f"OK: extracted {len(text)} chars from page 1")
    print("SELFTEST PASSED")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--domain", default="auto", choices=list(DOMAIN_SOURCES))
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--year", default=None, help="2020-2023 or 2020:")
    s.add_argument("--sort", default="relevance",
                   choices=["relevance", "citations", "date"])
    s.add_argument("--abstract", action="store_true")
    r = sub.add_parser("read")
    r.add_argument("target", help="pdf URL or local file path")
    r.add_argument("--pages", default=None, help="e.g. 1-3")
    r.add_argument("--out", default=None)
    sub.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "search":
        sys.exit(do_search(a.query, a.domain, a.limit, a.year, a.sort, a.abstract))
    if a.cmd == "read":
        sys.exit(do_read(a.target, a.pages, a.out))
    sys.exit(selftest())


if __name__ == "__main__":
    main()
