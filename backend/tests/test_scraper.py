"""Reading sources in full: open routes before the abstract, and indexing that survives dropped connections."""
import asyncio
import pytest
import utils.scraper as scraper
import utils.vectorstore as vectorstore

PAPER = "x" * scraper.MIN_TEXT

def test_arxiv_dois_and_links_are_read_from_arxiv():
    assert scraper.arxiv_link("https://doi.org/10.48550/arxiv.2607.14618") == "https://arxiv.org/pdf/2607.14618"
    assert scraper.arxiv_link("https://arxiv.org/pdf/2205.14135.pdf") == "https://arxiv.org/pdf/2205.14135"
    assert scraper.arxiv_link("https://doi.org/10.1109/CloudSummit.2026.00026") is None
    assert scraper.doi_of("https://doi.org/10.1007/978-3-031-85747-8_3") == "10.1007/978-3-031-85747-8_3"

def test_routes_are_tried_most_open_first(monkeypatch):
    tried = []
    monkeypatch.setattr(scraper, "_jina", lambda url, timeout: tried.append(url) or (PAPER if url.endswith(".pdf") else ""))
    source = {"url": "https://doi.org/10.1109/X.1", "pdf_url": "https://open.example.org/paper.pdf"}
    assert scraper.read_source(source) == (PAPER, "open-access PDF")
    assert tried == ["https://open.example.org/paper.pdf"]  # the open copy before the publisher's page

def test_unpaywall_runs_only_with_a_contact_email(monkeypatch):
    monkeypatch.setattr(scraper, "_jina", lambda url, timeout: PAPER if "oa-copy" in url else "")
    asked = []
    class Response:
        def json(self): return {"best_oa_location": {"url_for_pdf": "https://repo.example.org/oa-copy.pdf"}}
    monkeypatch.setattr(scraper.requests, "get", lambda url, params, timeout: asked.append(params) or Response())
    source = {"url": "https://doi.org/10.1007/abc"}
    monkeypatch.delenv("CONTACT_EMAIL", raising=False)
    assert scraper.read_source(source) == ("", "") and asked == []  # no email: Unpaywall isn't asked
    monkeypatch.setenv("CONTACT_EMAIL", "me@lab.org")
    assert scraper.read_source(source) == (PAPER, "Unpaywall") and asked == [{"email": "me@lab.org"}]

def test_tavily_reads_only_what_nothing_else_could_and_the_rest_keeps_its_abstract(monkeypatch):
    monkeypatch.setattr(scraper, "_jina", lambda url, timeout: PAPER if "arxiv.org" in url else "")
    monkeypatch.setattr(scraper, "unpaywall_link", lambda doi: None)
    extracted = []
    monkeypatch.setattr(scraper, "tavily_extract", lambda urls: extracted.append(urls) or {"https://blocked.example/b": PAPER})
    sources = [{"url": "https://doi.org/10.48550/arxiv.1.2", "summary": "s1"},
               {"url": "https://blocked.example/b", "summary": "s2"},
               {"url": "https://blocked.example/c", "summary": "s3"}]
    out = asyncio.run(scraper.process_sources_with_full_text(sources))
    assert [s["read_via"] for s in out] == ["arXiv", "Tavily", "abstract"]
    assert extracted == [["https://blocked.example/b", "https://blocked.example/c"]]  # one call, only the unread
    assert out[2]["full_text"] == "s3"

def test_block_pages_and_stubs_are_not_full_text(monkeypatch):
    monkeypatch.setattr(scraper, "_jina", lambda url, timeout: "")  # _jina drops anything under MIN_TEXT
    monkeypatch.setattr(scraper, "unpaywall_link", lambda doi: None)
    monkeypatch.setattr(scraper, "tavily_extract", lambda urls: {})
    out = asyncio.run(scraper.process_sources_with_full_text([{"url": "https://x.org/p", "summary": "abstract"}]))
    assert out[0]["read_via"] == "abstract"

def test_indexing_retries_dropped_connections_batch_by_batch(monkeypatch):
    async def no_wait(seconds):
        return None
    monkeypatch.setattr(vectorstore.asyncio, "sleep", no_wait)
    class Store:
        def __init__(self, failures): self.failures, self.batches = failures, []
        async def aadd_documents(self, docs):
            if self.failures:
                self.failures -= 1
                raise ConnectionResetError(54, "Connection reset by peer")
            self.batches.append(len(docs))
    store = Store(failures=2)
    assert asyncio.run(vectorstore.add_documents_reliably(store, list(range(70)), batch=32)) == 70
    assert store.batches == [32, 32, 6]  # every batch made it despite two resets
    with pytest.raises(ConnectionResetError):
        asyncio.run(vectorstore.add_documents_reliably(Store(failures=10), list(range(5))))  # gives up eventually
