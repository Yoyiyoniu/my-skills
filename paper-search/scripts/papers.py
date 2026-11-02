#!/usr/bin/env python3
"""papers.py — search official scholarly APIs and read a legal PDF.

Subcommands:
  search QUERY [--domain auto|ml|phys|math|bio|psy|chem]
               [--limit N] [--year 2020|2020-2024|2020-|:2019]
               [--sort relevance|citations|date] [--abstract]
  read PDF_URL_OR_PATH [--pages 1-3] [--out FILE]
  oa DOI
  selftest

Stdlib only. PDF text: pdftotext (poppler), pymupdf if pdftotext is missing.
Optional env: SEMANTIC_SCHOLAR_API_KEY, PAPER_SEARCH_EMAIL.
"""
import argparse
import json
import os
import re
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from xml.etree import ElementTree

UA = "paper-search-skill/1.0 (personal research tool)"
EMAIL = os.environ.get("PAPER_SEARCH_EMAIL", "papers-search@example.org")
S2_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY") or os.environ.get("S2_API_KEY")
SSL_CTX = ssl.create_default_context()
TIMEOUT = 30
NS = {
    "a": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def http_open(url, headers=None, retries=2, timeout=TIMEOUT):
    """GET url. Retries 429 and 5xx. Other HTTP errors propagate."""
    hdrs = {"User-Agent": UA}
    if headers:
        hdrs.update(headers)
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=hdrs)
        try:
            return urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX)
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500:
                raise
            last = e
            retry_after = e.headers.get("Retry-After") if e.headers else None
        except urllib.error.URLError as e:
            last = e
            retry_after = None
        if attempt + 1 < retries:
            delay = 1 + attempt
            if retry_after and str(retry_after).isdigit():
                delay = min(int(retry_after), 8)
            time.sleep(delay)
    raise last


def http_json(url, headers=None):
    with http_open(url, headers=headers) as r:
        return json.loads(r.read().decode())


def http_text(url, headers=None):
    with http_open(url, headers=headers) as r:
        return r.read().decode()


def get_json(base_url, params, headers=None):
    return http_json(base_url + "?" + urllib.parse.urlencode(params), headers)


def clean(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", text).strip()


def parse_year(year):
    """Return (start, end). None means open. Accepts 2020, 2020-2024, 2020-, 2020:, :2019."""
    if not year:
        return None, None
    text = year.strip().replace(":", "-")
    if "-" not in text:
        return text, text
    lo, _, hi = text.partition("-")
    return lo or None, hi or None


def s2_year(lo, hi):
    if lo and hi:
        return lo if lo == hi else f"{lo}-{hi}"
    if lo:
        return f"{lo}-"
    if hi:
        return f"-{hi}"
    return None


def prefer_exact_title(query, results):
    key = re.sub(r"[^a-z0-9]+", " ", query.lower()).strip()

    def norm(title):
        return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()

    exact = [r for r in results if norm(r["title"]) == key]
    if not exact:
        return results
    rest = [r for r in results if norm(r["title"]) != key]
    return exact + rest


# ---------------------------------------------------------------- arXiv ----
def search_arxiv(query, limit, year, sort):
    q = query.replace('"', "")
    sq = f'all:"{q}"' if " " in q else f"all:{q}"
    lo, hi = parse_year(year)
    if lo or hi:
        start = f"{int(lo):04d}01010000" if lo else "199101010000"
        end = f"{int(hi):04d}12312359" if hi else "300012312359"
        sq += f" AND submittedDate:[{start} TO {end}]"
    sort_by = {"date": "submittedDate"}.get(sort, "relevance")
    params = {
        "search_query": sq,
        "start": 0,
        "max_results": limit,
        "sortBy": sort_by,
    }
    xml = http_text("https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params))
    root = ElementTree.fromstring(xml)
    out = []
    for e in root.findall("a:entry", NS):
        title_el = e.find("a:title", NS)
        published = e.find("a:published", NS)
        summary = e.find("a:summary", NS)
        id_el = e.find("a:id", NS)
        if title_el is None or id_el is None or not (title_el.text and id_el.text):
            continue
        arxiv_id = re.sub(r"v\d+$", "", id_el.text.rsplit("/", 1)[-1])
        doi_el = e.find("arxiv:doi", NS)
        doi = clean(doi_el.text) if doi_el is not None and doi_el.text else ""
        if not doi and re.fullmatch(r"\d{4}\.\d{4,5}", arxiv_id):
            doi = f"10.48550/arXiv.{arxiv_id}"
        out.append({
            "title": clean(title_el.text),
            "year": (published.text or "")[:4] if published is not None and published.text else "",
            "doi": doi,
            "citations": "",
            "pdf": f"https://arxiv.org/pdf/{arxiv_id}",
            "abstract": clean(summary.text if summary is not None else ""),
            "source": "arXiv",
        })
    return out


# ------------------------------------------------------ Semantic Scholar ---
def s2_headers():
    return {"x-api-key": S2_KEY} if S2_KEY else None


def search_s2(query, limit, year, sort):
    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": "title,abstract,year,externalIds,citationCount,openAccessPdf,venue",
        "sort": {"citations": "citationCount:desc", "date": "publicationDate:desc"}.get(
            sort, "relevance:desc"),
    }
    year_param = s2_year(*parse_year(year))
    if year_param:
        params["year"] = year_param
    data = get_json(
        "https://api.semanticscholar.org/graph/v1/paper/search", params, s2_headers())
    out = []
    for p in data.get("data") or []:
        out.append({
            "title": clean(p.get("title")),
            "year": p.get("year") or "",
            "doi": (p.get("externalIds") or {}).get("DOI", "") or "",
            "citations": p.get("citationCount") or 0,
            "pdf": ((p.get("openAccessPdf") or {}).get("url") or ""),
            "abstract": clean(p.get("abstract")),
            "source": "SemanticScholar",
        })
    return out


# ------------------------------------------------------------ OpenAlex ----
def openalex_abstract(inv):
    if not inv:
        return ""
    words = {}
    for word, positions in inv.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words))


def search_openalex(query, limit, year, sort):
    params = {
        "search": query,
        "per_page": min(limit, 100),
        "mailto": EMAIL,
        "sort": {"citations": "cited_by_count:desc", "date": "publication_date:desc"}.get(
            sort, "relevance_score:desc"),
    }
    lo, hi = parse_year(year)
    filters = []
    if lo:
        filters.append(f"from_publication_date:{lo}-01-01")
    if hi:
        filters.append(f"to_publication_date:{hi}-12-31")
    if filters:
        params["filter"] = ",".join(filters)
    data = get_json("https://api.openalex.org/works", params)
    out = []
    for w in data.get("results") or []:
        loc = w.get("primary_location") or {}
        pdf = loc.get("pdf_url") or ""
        if not pdf:
            for candidate in w.get("locations") or []:
                if candidate.get("pdf_url"):
                    pdf = candidate["pdf_url"]
                    break
        out.append({
            "title": clean(w.get("display_name")),
            "year": w.get("publication_year") or "",
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
            "citations": w.get("cited_by_count") or 0,
            "pdf": pdf,
            "abstract": openalex_abstract(w.get("abstract_inverted_index")),
            "source": "OpenAlex",
        })
    return out


# ----------------------------------------------------------- Europe PMC ---
def search_europepmc(query, limit, year, sort):
    q = f"({query})"
    lo, hi = parse_year(year)
    if lo and hi and lo == hi:
        q += f" AND (PUB_YEAR:{lo})"
    elif lo or hi:
        q += f" AND (PUB_YEAR:[{lo or '1900'} TO {hi or '2100'}])"
    params = {
        "query": q,
        "format": "json",
        "resultType": "core",
        "pageSize": min(limit, 100),
    }
    sort_name = {"citations": "CITED", "date": "DATE"}.get(sort)
    if sort_name:
        params["sort"] = sort_name
    data = get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search", params)
    out = []
    for hit in data.get("resultList", {}).get("result", []):
        pdf_link = ""
        for u in hit.get("fullTextUrlList", {}).get("fullTextUrl", []):
            if u.get("documentStyle") == "pdf":
                pdf_link = u.get("url", "")
                break
        if pdf_link.startswith("http://europepmc.org"):
            pdf_link = "https://" + pdf_link[len("http://"):]
        out.append({
            "title": clean(hit.get("title")),
            "year": hit.get("pubYear", "") or "",
            "doi": hit.get("doi", "") or "",
            "citations": hit.get("citedByCount", 0) or 0,
            "pdf": pdf_link,
            "abstract": clean(hit.get("abstractText")),
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
    "auto": (search_s2, search_openalex),
}


def source_chain(domain, sort):
    chain = list(DOMAIN_SOURCES[domain])
    if search_openalex not in chain:
        chain.append(search_openalex)
    if sort == "citations":
        # arXiv has no citation counts. Keep it only as the last resort.
        chain = [fn for fn in chain if fn is not search_arxiv] + [
            fn for fn in chain if fn is search_arxiv]
    ordered = []
    for fn in chain:
        if fn not in ordered:
            ordered.append(fn)
    return ordered


def do_search(query, domain, limit, year, sort, show_abstract):
    # Pull a few extra on relevance so an exact title match can move to the top
    # even when --limit is smaller than where the API ranked it.
    fetch = max(limit, 8) if sort == "relevance" else limit
    results, err = [], None
    for fn in source_chain(domain, sort):
        if results:
            break
        try:
            results = fn(query, fetch, year, sort)
        except Exception as e:
            err = (err + "; " if err else "") + f"{fn.__name__}: {e}"
            results = []
    if not results:
        print(f"ERROR: all sources failed — {err}", file=sys.stderr)
        return 1
    if err:
        print(f"NOTE: fallback used ({err})", file=sys.stderr)
    if sort == "relevance":
        results = prefer_exact_title(query, results)
    print_results(results[:limit], show_abstract)
    return 0


def print_results(results, show_abstract):
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}  [{r['source']}]")
        print(f"   year={r['year']}  doi={r['doi'] or '-'}  citations={r['citations'] or '-'}")
        print(f"   pdf={r['pdf'] or '(no open PDF — run: papers.py oa <DOI>)'}")
        if show_abstract and r["abstract"]:
            abstract = r["abstract"]
            if len(abstract) > 2000:
                abstract = abstract[:2000] + "…"
            print(f"   abstract: {abstract}")


# ---------------------------------------------------------------- read ----
def rewrite_pdf_url(url):
    match = re.match(r"https?://(?:www\.)?arxiv\.org/abs/([^?#]+)", url)
    if match:
        return "https://arxiv.org/pdf/" + match.group(1)
    return url


def download_pdf(url, path):
    req_headers = {"User-Agent": UA, "Accept": "application/pdf,*/*"}
    with http_open(url, headers=req_headers, retries=2, timeout=90) as r, open(path, "wb") as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)


def extract_pdf_text(path, pages):
    lo = hi = None
    if pages:
        left, _, right = pages.partition("-")
        lo, hi = left, (right or left)
    cmd = ["pdftotext"]
    if pages:
        cmd += ["-f", lo, "-l", hi]
    cmd += [path, "-"]
    pdftotext_empty = False
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
        pdftotext_empty = r.returncode == 0
    except FileNotFoundError:
        pass
    try:
        import pymupdf
    except ImportError:
        if pdftotext_empty:
            raise SystemExit("ERROR: PDF has no extractable text (likely scanned).")
        raise SystemExit(
            "ERROR: pdftotext not found and pymupdf is not installed. "
            "Install poppler-utils.")
    doc = pymupdf.open(path)
    if pages:
        rng = range(int(lo) - 1, int(hi))
    else:
        rng = range(doc.page_count)
    return "".join(doc[i].get_text() for i in rng if 0 <= i < doc.page_count)


def do_read(target, pages, out_file):
    path = target
    if re.match(r"^https?://", target):
        target = rewrite_pdf_url(target)
        path = os.path.join(tempfile.gettempdir(), "paper-search.pdf")
        download_pdf(target, path)
    with open(path, "rb") as f:
        if not f.read(1024).lstrip().startswith(b"%PDF"):
            raise SystemExit(
                f"ERROR: not a PDF ({target}). Landing page or paywall. "
                "Run: papers.py oa <DOI> and read the pdf= URL.")
    text = extract_pdf_text(path, pages)
    if not text.strip():
        raise SystemExit("ERROR: PDF downloaded but no text extracted (scanned pages).")
    if out_file:
        parent = os.path.dirname(out_file)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(out_file, "w") as f:
            f.write(text)
        print(f"saved {len(text)} chars to {out_file}")
    else:
        print(text)
    return 0


# ------------------------------------------------------------------- oa ----
def normalize_doi(doi):
    doi = doi.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.I)
    return doi


def do_oa(doi):
    doi = normalize_doi(doi)
    arxiv = re.fullmatch(r"10\.48550/arxiv\.(\d{4}\.\d{4,5})", doi, flags=re.I)
    url = "https://api.unpaywall.org/v2/" + urllib.parse.quote(doi) + "?" + urllib.parse.urlencode(
        {"email": EMAIL})
    try:
        data = http_json(url)
    except urllib.error.HTTPError as e:
        if e.code == 404 and arxiv:
            pdf = f"https://arxiv.org/pdf/{arxiv.group(1)}"
            print(f"doi={doi}")
            print("is_oa=True")
            print(f"pdf={pdf}")
            print(f"url=https://arxiv.org/abs/{arxiv.group(1)}")
            print("host=repository")
            return 0
        print(f"ERROR: unpaywall {e.code} for {doi}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"ERROR: unpaywall unreachable ({e.reason})", file=sys.stderr)
        return 1
    locations = data.get("oa_locations") or []
    best = data.get("best_oa_location") or {}
    pdf = best.get("url_for_pdf") or ""
    if not pdf:
        for loc in locations:
            if loc.get("url_for_pdf"):
                pdf = loc["url_for_pdf"]
                best = loc
                break
    print(f"doi={doi}")
    print(f"is_oa={bool(data.get('is_oa'))}")
    print(f"pdf={pdf or '-'}")
    print(f"url={best.get('url') or '-'}")
    print(f"host={best.get('host_type') or '-'}")
    return 0


# -------------------------------------------------------------- selftest --
def selftest():
    assert parse_year("2020-2024") == ("2020", "2024")
    assert parse_year("2020:") == ("2020", None)
    assert parse_year("2020-") == ("2020", None)
    assert parse_year("2020") == ("2020", "2020")
    assert parse_year(":2019") == (None, "2019")
    assert s2_year("2020", "2024") == "2020-2024"
    assert s2_year("2020", None) == "2020-"
    ranked = prefer_exact_title("attention is all you need", [
        {"title": "Tool Attention Is All You Need"},
        {"title": "Attention Is All You Need"},
    ])
    assert ranked[0]["title"] == "Attention Is All You Need"
    chain = source_chain("auto", "relevance")
    assert chain[0] is search_s2 and chain[1] is search_openalex and len(chain) == 2
    cited = source_chain("ml", "citations")
    assert cited == [search_s2, search_openalex, search_arxiv]
    print("OK: offline")

    print("== search arXiv (ml) ==")
    results = search_arxiv("attention is all you need", 5, None, "relevance")
    assert results, "arxiv search returned nothing"
    assert any(r["title"] == "Attention Is All You Need" for r in results), results[0]["title"]
    print(f"OK: {len(results)} results, includes the transformer paper")

    print("== search general (Semantic Scholar, else OpenAlex) ==")
    import io
    from contextlib import redirect_stderr, redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(io.StringIO()):
        rc = do_search("CRISPR base editing", "auto", 3, "2020-2024", "relevance", False)
    assert rc == 0, "auto search failed on every source"
    lines = buf.getvalue()
    assert "CRISPR" in lines.upper() or "crispr" in lines.lower(), lines
    years = [int(y) for y in re.findall(r"year=(\d{4})", lines)]
    assert years and all(2020 <= y <= 2024 for y in years), lines
    print(f"OK: year filter held ({years})")

    print("== read arXiv page 1 ==")
    text = None
    path = os.path.join(tempfile.gettempdir(), "paper-search-selftest.pdf")
    download_pdf("https://arxiv.org/pdf/1706.03762", path)
    text = extract_pdf_text(path, "1")
    assert "Attention" in text, "page 1 did not contain the title"
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
    s.add_argument("--limit", type=int, default=8)
    s.add_argument("--year", default=None, help="2020, 2020-2024, 2020-, or :2019")
    s.add_argument("--sort", default="relevance", choices=["relevance", "citations", "date"])
    s.add_argument("--abstract", action="store_true")
    r = sub.add_parser("read")
    r.add_argument("target", help="pdf URL or local file path")
    r.add_argument("--pages", default=None, help="e.g. 1-3")
    r.add_argument("--out", default=None)
    o = sub.add_parser("oa")
    o.add_argument("doi", help="DOI or https://doi.org/...")
    sub.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "search":
        sys.exit(do_search(a.query, a.domain, a.limit, a.year, a.sort, a.abstract))
    if a.cmd == "read":
        sys.exit(do_read(a.target, a.pages, a.out))
    if a.cmd == "oa":
        sys.exit(do_oa(a.doi))
    sys.exit(selftest())


if __name__ == "__main__":
    main()
