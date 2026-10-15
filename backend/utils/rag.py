"""Retrieval for the source chat: query rewriting, hybrid dense + BM25 search,
reciprocal rank fusion and LLM reranking."""
import re
import json
import math
import asyncio
import hashlib
from collections import Counter
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import ainvoke_llm
from utils.vectorstore import get_qdrant_client, get_vector_store, collection_exists

# A passage: {"text", "title", "url", "source", "year"}

_TOKEN = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")
_STOPWORDS = {"a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are", "was", "were",
              "how", "did", "do", "does", "what", "which", "they", "it", "this", "that", "by", "as", "be", "at"}

def tokenize(text: str):
    """Lowercase word/number tokens; "99%" -> "99", "98.08%" -> "98.08"."""
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOPWORDS]

def passage_key(p: dict) -> str:
    return hashlib.sha1(f"{p.get('url')}|{p['text'][:300]}".encode()).hexdigest()

def bm25_rank(query: str, passages: list, k: int = 20, k1: float = 1.5, b: float = 0.75) -> list:
    """Sparse keyword ranking: catches exact terms (numbers, model names, metrics) that embeddings miss."""
    docs = [tokenize(f"{p.get('title', '')} {p['text']}") for p in passages]
    if not docs:
        return []
    avgdl = sum(len(d) for d in docs) / len(docs) or 1
    df = Counter(t for d in docs for t in set(d))
    idf = {t: math.log(1 + (len(docs) - f + 0.5) / (f + 0.5)) for t, f in df.items()}
    q = tokenize(query)
    scores = []
    for i, d in enumerate(docs):
        tf = Counter(d)
        s = sum(idf[t] * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / avgdl)) for t in q if t in tf)
        if s > 0:
            scores.append((s, i))
    return [passages[i] for _, i in sorted(scores, reverse=True)[:k]]

def reciprocal_rank_fusion(*rankings: list, k: int = 60) -> list:
    """Merge ranked passage lists; items ranked high in any list rise to the top."""
    scores, by_key = {}, {}
    for ranking in rankings:
        for rank, p in enumerate(ranking):
            key = passage_key(p)
            by_key[key] = p
            scores[key] = scores.get(key, 0) + 1 / (k + rank + 1)
    return [by_key[key] for key in sorted(scores, key=scores.get, reverse=True)]

# --- Corpus ---------------------------------------------------------------------

_chunk_cache: dict = {}

def load_chunks(collection: str) -> list:
    """Every indexed chunk of a research session (cached until the collection changes)."""
    client = get_qdrant_client()
    count = client.count(collection).count
    cached = _chunk_cache.get(collection)
    if cached and cached[0] == count:
        return cached[1]
    passages, offset = [], None
    while True:
        points, offset = client.scroll(collection, limit=500, offset=offset, with_payload=True, with_vectors=False)
        for p in points:
            meta = p.payload.get("metadata", {})
            passages.append({"text": p.payload.get("page_content", ""), "title": meta.get("title", ""),
                             "url": meta.get("url"), "source": meta.get("source"), "year": meta.get("year")})
        if offset is None:
            break
    _chunk_cache[collection] = (count, passages)
    return passages

def source_abstracts(sources: list) -> list:
    """Abstract/snippet of every retrieved source, so sources not read in full are still searchable."""
    return [{"text": s.get("summary") or "", "title": s.get("title", ""), "url": s.get("url"),
             "source": s.get("source"), "year": s.get("year")} for s in sources if s.get("summary")]

async def dense_search(collection: str, query: str, k: int = 20) -> list:
    docs = await get_vector_store(collection).asimilarity_search(query, k=k)
    return [{"text": d.page_content, "title": d.metadata.get("title", ""), "url": d.metadata.get("url"),
             "source": d.metadata.get("source"), "year": d.metadata.get("year")} for d in docs]

# --- LLM steps ------------------------------------------------------------------

def _json_from(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group(0)) if match else None

async def rewrite_query(question: str, history: list, topic: str, summary: str) -> str:
    """Standalone, keyword-rich search query: resolves "they"/"it" from the conversation, fixes typos."""
    convo = "\n".join(f"{m['role']}: {m['content'][:600]}" for m in history[-6:])
    prompt = (
        f"Research topic: {topic}\n\nResearch summary:\n{(summary or '')[:1500]}\n\n"
        f"Conversation so far:\n{convo or '(none)'}\n\nLatest question: {question}"
    )
    try:
        response = await ainvoke_llm([
            SystemMessage(content=(
                "Rewrite the user's latest question as one standalone search query for finding passages in research papers. "
                "Resolve pronouns like 'they' or 'it' using the conversation and summary, fix typos, and keep exact numbers, "
                "names, metrics and technical terms. Return only the query, nothing else."
            )),
            HumanMessage(content=prompt),
        ], agent_name="retrieval", temperature=0)
        rewritten = response.content.strip().strip('"').splitlines()[0].strip()
        return rewritten or question
    except Exception as e:
        print(f"[RAG] query rewrite failed: {e}")
        return question

async def rerank(question: str, candidates: list, top_n: int = 6, per_source: int = 2) -> list:
    """Order candidates by how well they answer the question; at most `per_source` passages per source."""
    if not candidates:
        return []
    listing = "\n\n".join(f"<{i}> {c['title']}\n{c['text'][:900]}" for i, c in enumerate(candidates))
    order = list(range(len(candidates)))
    try:
        response = await ainvoke_llm([
            SystemMessage(content=(
                "Rate how useful each passage is for answering the question, from 0 (irrelevant) to 10 (directly answers it). "
                'Return ONLY JSON: {"scores": [[passage_id, score], ...]} covering every passage.'
            )),
            HumanMessage(content=f"Question: {question}\n\nPassages:\n{listing}"),
        ], agent_name="retrieval", temperature=0)
        scores = {int(i): float(s) for i, s in (_json_from(response.content) or {}).get("scores", [])}
        # Highest score first; the fused rank breaks ties. Clearly irrelevant passages are dropped.
        order = sorted((i for i in order if scores.get(i, 0) >= 3), key=lambda i: (-scores.get(i, 0), i)) or order
    except Exception as e:
        print(f"[RAG] rerank failed, keeping fused order: {e}")

    picked, per = [], Counter()
    for i in order:
        url = candidates[i].get("url")
        if per[url] < per_source:
            picked.append(candidates[i])
            per[url] += 1
        if len(picked) == top_n:
            break
    return picked

async def retrieve(collection: str, question: str, history: list, topic: str, summary: str, sources: list):
    """Hybrid retrieval for one chat question. Returns (search query used, best passages)."""
    query = await rewrite_query(question, history, topic, summary)
    has_index = await asyncio.to_thread(collection_exists, collection)

    dense = await dense_search(collection, query) if has_index else []
    corpus = (await asyncio.to_thread(load_chunks, collection) if has_index else []) + source_abstracts(sources)
    sparse = bm25_rank(query, corpus)

    candidates = reciprocal_rank_fusion(dense, sparse)[:24]
    return query, await rerank(query, candidates)
