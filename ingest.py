from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import numpy as np
import requests
import toml
import trafilatura
from bs4 import BeautifulSoup
from openai import OpenAI

ROOT = Path(__file__).parent
SEEDS_FILE = ROOT / "seeds.txt"
BOT_TRUTHS_FILE = ROOT / "ub-basel-bot-wahrheiten.md"
CURATED_EXTRA_FILES = [
    ("glossar-und-synonyme.md", "glossary", "high"),
    ("personen-und-kontakte.md", "contacts", "high"),
]
CLEAN_DIR = ROOT / "data" / "cleaned"
VECTOR_DIR = ROOT / "vectorstore"
INDEX_NPZ = VECTOR_DIR / "index.npz"
DOCS_JSONL = VECTOR_DIR / "docs.jsonl"
DISCOVERED_URLS = VECTOR_DIR / "discovered_urls.txt"

CLEAN_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_DOMAIN = "ub.unibas.ch"
DEFAULT_MAX_PAGES = 250
REQUEST_DELAY_SECONDS = 0.5

# Sicherheitsgrenze: OpenAI-Embeddings erlauben max. 8192 Tokens.
# Zeichenlimit ist konservativ und verhindert Fehler bei langen Tabellen/Listen.
MAX_EMBED_CHARS = 3000

SKIP_EXTENSIONS = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".zip", ".ics",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".mp4", ".mp3"
)

SKIP_URL_PATTERNS = (
    "mailto:",
    "tel:",
    "javascript:",
    "#",
    "/typo3/",
    "/intranet",
    "/login",
    "/logout",
    "/suche?",
    "?",
)

# Standardmäßig ausschließen: temporäre und präsentationskritisch rauschanfällige Inhalte.
# Für einen Servicebot sind Fach-/Service-/Recherche-/Standortseiten wichtiger.
EXCLUDE_URL_PATTERNS = (
    "/de/aktuell",
    "/en/current",
    "/de/news",
    "/en/news",
    "/de/veranstaltungen",
    "/en/events",
    "/de/ausstellungen",
    "/en/exhibitions",
    "/de/ub-tage",
    "/en/ub-days",
    "/newsletter",
    "/blog",
)

LOW_VALUE_PATTERNS = EXCLUDE_URL_PATTERNS

NOISE_LINES = (
    "Zum Seitenanfang",
    "Diese Seite teilen",
    "Social Media",
    "Newsletter",
    "Cookie",
    "Navigation",
    "Menü",
    "Suche",
    "Search",
)


def get_secret(name: str, default: str | None = None) -> str:
    if os.environ.get(name):
        return os.environ[name]
    secrets_path = ROOT / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            value = toml.load(secrets_path).get(name)
            if value:
                return str(value)
        except Exception:
            pass
    if default is not None:
        return default
    raise KeyError(f"{name} nicht gefunden. Bitte in .streamlit/secrets.toml oder als Umgebungsvariable setzen.")


OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
EMBEDDING_MODEL = get_secret("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
client = OpenAI(api_key=OPENAI_API_KEY)


def stable_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_url(url: str) -> str | None:
    url = urldefrag(url)[0].strip()
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    if parsed.netloc and parsed.netloc != ALLOWED_DOMAIN:
        return None

    # Query-Parameter entfernen, damit keine Filter-/Suchvarianten explodieren.
    parsed = parsed._replace(query="")
    normalized = parsed.geturl()

    if any(normalized.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
        return None
    if any(pattern in normalized for pattern in SKIP_URL_PATTERNS):
        return None

    # Nur UB-Hauptdomain.
    if urlparse(normalized).netloc != ALLOWED_DOMAIN:
        return None

    return normalized


def read_seeds() -> list[str]:
    if not SEEDS_FILE.exists():
        return ["https://ub.unibas.ch/de/", "https://ub.unibas.ch/en/"]
    seeds = []
    for line in SEEDS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            normalized = normalize_url(line)
            if normalized:
                seeds.append(normalized)
    return seeds


def url_priority(url: str) -> int:
    """Priorisiert Seiten, die für Servicebot/Fachauskunft wichtig sind."""
    top_terms = [
        "/de/fachgebiete", "/de/psychologie", "/de/medizin", "/de/theologie",
        "/de/wirtschaft", "/de/rechtswissenschaft", "/de/philosophie",
        "/de/paedagogik", "/de/soziologie", "/de/politikwissenschaft",
        "/de/germanistik", "/de/geschichte", "/de/kunstgeschichte",
        "/de/musikwissenschaft", "/de/medienwissenschaft", "/de/biowissenschaften",
        "/de/chemie", "/de/physik", "/de/mathematik", "/de/informatik",
        "/de/geowissenschaften", "/de/open-science", "/de/open-access",
        "/de/kontakt", "/de/reglemente-gebuehren",
    ]
    high_terms = [
        "/de/service", "/de/recherche", "/de/standorte", "/de/ub-",
        "/de/anmelden", "/de/oeffnungszeiten", "/de/bibliothekskataloge",
        "/de/datenbanken", "/de/find-", "/de/online-datenbanken",
        "/de/schulungen", "/de/arbeitsplaetze", "/de/kopieren",
        "/de/ki", "/de/digitale-sammlungen", "/de/zeitungen",
        "/en/service", "/en/research", "/en/subjects", "/en/locations",
    ]
    medium_terms = [
        "/de/sammlungen", "/de/historische-bestaende", "/de/organisation",
        "/de/bibliotheken-in-basel", "/de/bibliotheksnetz",
    ]
    if any(t in url for t in top_terms):
        return 0
    if any(t in url for t in high_terms):
        return 1
    if any(t in url for t in medium_terms):
        return 2
    if any(t in url for t in EXCLUDE_URL_PATTERNS):
        return 9
    return 4



def extract_links(base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        full = urljoin(base_url, href)
        normalized = normalize_url(full)
        if normalized:
            links.append(normalized)
    # Deduplizieren, aber Reihenfolge erhalten
    seen = set()
    out = []
    for link in links:
        if link not in seen:
            seen.add(link)
            out.append(link)
    return out


def fetch_html(url: str) -> str:
    headers = {"User-Agent": "UB-Basel-Servicebot-MVP/0.2; broad internal crawl"}
    response = requests.get(url, headers=headers, timeout=25)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        raise ValueError(f"Kein HTML: {content_type}")
    return response.text


def discover_urls(max_pages: int, include_low_value: bool = False) -> list[str]:
    seeds = read_seeds()
    queue = deque(seeds)
    seen = set(seeds)
    discovered = []

    while queue and len(discovered) < max_pages:
        # Priorisierte Auswahl aus Queue: Service/Fach/Standort vor Aktuell.
        queue = deque(sorted(list(queue), key=url_priority))
        url = queue.popleft()

        if (not include_low_value) and any(pattern in url for pattern in EXCLUDE_URL_PATTERNS):
            continue

        print(f"Discover [{len(discovered)+1}/{max_pages}]: {url}")
        try:
            html = fetch_html(url)
        except Exception as exc:
            print(f"  Skip: {exc}")
            continue

        discovered.append(url)

        for link in extract_links(url, html):
            if link not in seen:
                seen.add(link)
                queue.append(link)

        time.sleep(REQUEST_DELAY_SECONDS)

    DISCOVERED_URLS.write_text("\n".join(discovered), encoding="utf-8")
    return discovered


def extract_clean_text(url: str) -> str:
    headers = {"User-Agent": "UB-Basel-Servicebot-MVP/0.2; broad internal crawl"}
    response = requests.get(url, headers=headers, timeout=25)
    response.raise_for_status()

    extracted = trafilatura.extract(
        response.text,
        include_links=True,
        include_tables=True,
        output_format="markdown",
        url=url,
    )

    if not extracted:
        raise ValueError("Kein verwertbarer Text extrahiert")
    return extracted.strip()


def normalize_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    filtered = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped and any(noise.lower() == stripped.lower() for noise in NOISE_LINES):
            continue
        filtered.append(line)
    text = "\n".join(filtered)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def chunk_markdown_by_headings(text: str, max_chars: int = 2600, min_chars: int = 160) -> list[str]:
    text = normalize_markdown(text)
    lines = text.split("\n")
    sections = []
    current = []

    for line in lines:
        is_heading = line.startswith("## ") or line.startswith("### ")
        if is_heading and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        sections.append("\n".join(current).strip())

    chunks = []
    for section in sections:
        if len(section) <= max_chars:
            if len(section) >= min_chars:
                chunks.append(section)
            continue

        heading_lines = [ln for ln in section.split("\n")[:6] if ln.startswith("#")]
        heading_context = "\n".join(heading_lines).strip()
        paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
        buf = heading_context

        for paragraph in paragraphs:
            if paragraph in heading_context:
                continue
            candidate = (buf + "\n\n" + paragraph).strip()
            if len(candidate) <= max_chars:
                buf = candidate
            else:
                if len(buf) >= min_chars:
                    chunks.append(buf)
                buf = (heading_context + "\n\n" + paragraph).strip()

        if len(buf) >= min_chars:
            chunks.append(buf)

    seen = set()
    out = []
    for chunk in chunks:
        key = stable_id(chunk)
        if key not in seen:
            seen.add(key)
            out.append(chunk)
    return out


def split_for_embedding_safety(doc: dict, max_chars: int = MAX_EMBED_CHARS) -> list[dict]:
    """Teilt überlange Chunks zusätzlich, bevor sie an das Embedding-Modell gehen."""
    content = doc.get("text", "")
    if len(content) <= max_chars:
        return [doc]

    parts = [p.strip() for p in content.split("\n\n") if p.strip()]
    chunks = []
    buf = ""

    for part in parts:
        candidate = (buf + "\n\n" + part).strip() if buf else part
        if len(candidate) <= max_chars:
            buf = candidate
        else:
            if buf:
                chunks.append(buf)
            if len(part) > max_chars:
                for i in range(0, len(part), max_chars):
                    chunks.append(part[i:i + max_chars])
                buf = ""
            else:
                buf = part

    if buf:
        chunks.append(buf)

    out = []
    for i, chunk_text in enumerate(chunks):
        new_doc = dict(doc)
        new_doc["text"] = chunk_text
        new_doc["id"] = stable_id(f"{doc.get('id')}|safe|{i}|{chunk_text[:80]}")
        new_doc["chunk"] = f"{doc.get('chunk')}.{i}"
        out.append(new_doc)

    return out


def enforce_embedding_safety(docs: list[dict]) -> list[dict]:
    safe_docs = []
    split_count = 0
    for doc in docs:
        split_docs = split_for_embedding_safety(doc)
        if len(split_docs) > 1:
            split_count += 1
        safe_docs.extend(split_docs)
    if split_count:
        print(f"Embedding-Sicherheitscheck: {split_count} überlange Chunks zusätzlich geteilt.")
    return safe_docs


def embed_texts(texts: list[str], batch_size: int = 16) -> np.ndarray:
    all_vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        vectors = np.array([item.embedding for item in result.data], dtype=np.float32)
        all_vectors.append(vectors)
    arr = np.vstack(all_vectors)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    return arr / np.maximum(norms, 1e-12)


def ingest_extra_curated_files(docs: list[dict]) -> None:
    """Indexiert kuratierte Zusatzdateien mit hoher Priorität."""
    for filename, source_type, priority in CURATED_EXTRA_FILES:
        path = ROOT / filename
        if not path.exists():
            print(f"Warnung: {filename} nicht gefunden.")
            continue
        text = path.read_text(encoding="utf-8")
        chunks = chunk_markdown_by_headings(text, max_chars=2000)
        (CLEAN_DIR / f"00_{filename}").write_text(text, encoding="utf-8")
        for i, chunk in enumerate(chunks):
            docs.append({
                "id": stable_id(f"{source_type}|{i}|{chunk}"),
                "text": chunk,
                "source": f"Kuratierte Datei: {filename}",
                "source_type": source_type,
                "priority": priority,
                "chunk": i,
            })
        print(f"Kuratierte Datei {filename}: {len(chunks)} Chunks")


def collect_documents(max_pages: int, include_low_value: bool) -> list[dict]:
    docs = []

    if BOT_TRUTHS_FILE.exists():
        text = BOT_TRUTHS_FILE.read_text(encoding="utf-8")
        chunks = chunk_markdown_by_headings(text, max_chars=2000)
        (CLEAN_DIR / "00_bot_wahrheiten.md").write_text(text, encoding="utf-8")
        for i, chunk in enumerate(chunks):
            docs.append({
                "id": stable_id(f"bot_truths|{i}|{chunk}"),
                "text": chunk,
                "source": "Interne Richtlinie: ub-basel-bot-wahrheiten.md",
                "source_type": "bot_truths",
                "priority": "high",
                "chunk": i,
            })
        print(f"Master-Quelle: {len(chunks)} Chunks")

    ingest_extra_curated_files(docs)

    urls = discover_urls(max_pages=max_pages, include_low_value=include_low_value)

    for n, url in enumerate(urls, start=1):
        print(f"Ingest [{n}/{len(urls)}]: {url}")
        try:
            text = normalize_markdown(extract_clean_text(url))
        except Exception as exc:
            print(f"  Fehler: {exc}")
            continue

        filename = stable_id(url)[:12] + ".md"
        (CLEAN_DIR / filename).write_text(f"# Quelle\n\n{url}\n\n# Inhalt\n\n{text}", encoding="utf-8")

        chunks = chunk_markdown_by_headings(text, max_chars=2000)
        rank = url_priority(url)
        if rank == 0:
            page_priority = "medium_high"
        elif rank == 1:
            page_priority = "medium_high"
        elif rank == 2:
            page_priority = "medium"
        elif rank >= 9:
            page_priority = "very_low"
        else:
            page_priority = "low"

        for i, chunk in enumerate(chunks):
            docs.append({
                "id": stable_id(f"{url}|{i}|{chunk}"),
                "text": chunk,
                "source": url,
                "source_type": "web",
                "priority": page_priority,
                "chunk": i,
            })

        print(f"  {len(chunks)} Chunks")

    return docs


def save_index(docs: list[dict]) -> None:
    if not docs:
        raise RuntimeError("Keine Dokumente zum Indexieren gefunden.")

    texts = [doc["text"] for doc in docs]
    embeddings = embed_texts(texts)

    np.savez_compressed(INDEX_NPZ, embeddings=embeddings)

    with DOCS_JSONL.open("w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print(f"Index gespeichert: {INDEX_NPZ}")
    print(f"Dokumente gespeichert: {DOCS_JSONL}")
    print(f"Chunks total: {len(docs)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Bestehenden lokalen Index löschen")
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES, help="Maximale Anzahl zu crawlender HTML-Seiten")
    parser.add_argument("--include-low-value", action="store_true", help="Auch News-/Event-nahe Seiten stärker zulassen")
    args = parser.parse_args()

    if args.reset:
        for p in [INDEX_NPZ, DOCS_JSONL, DISCOVERED_URLS]:
            if p.exists():
                p.unlink()
        print("Alter Index gelöscht.")

    docs = collect_documents(max_pages=args.max_pages, include_low_value=args.include_low_value)
    save_index(docs)
    print("Index fertig.")


if __name__ == "__main__":
    main()
