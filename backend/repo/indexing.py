"""Index a repository's files into Qdrant so the writer can cite the code.

Every chunk carries the repository's url, the same url as its entry in raw_sources, so a
code passage is cited as the repository's reference number."""
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from repo.scanner import RepoSnapshot
from utils.vectorstore import ensure_collection, get_vector_store

MAX_CHUNKS = 1500  # embedding cost guard for very large repositories

# Split on functions and classes rather than mid-statement where the splitter knows the language
_SPLITTER_LANGUAGES = {
    "Python": Language.PYTHON, "Jupyter Notebook": Language.PYTHON, "JavaScript": Language.JS,
    "TypeScript": Language.TS, "Java": Language.JAVA, "Kotlin": Language.KOTLIN, "Go": Language.GO,
    "Rust": Language.RUST, "C": Language.C, "C++": Language.CPP, "C#": Language.CSHARP,
    "Ruby": Language.RUBY, "PHP": Language.PHP, "Swift": Language.SWIFT, "Scala": Language.SCALA,
    "R": Language.R, "Lua": Language.LUA, "Solidity": Language.SOL, "Markdown": Language.MARKDOWN,
}


def _splitter(language: str, cache: dict) -> RecursiveCharacterTextSplitter:
    if language not in cache:
        lang = _SPLITTER_LANGUAGES.get(language)
        cache[language] = (RecursiveCharacterTextSplitter.from_language(lang, chunk_size=1200, chunk_overlap=150)
                           if lang else RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150))
    return cache[language]


def chunk_repo(snapshot: RepoSnapshot, repo_name: str, repo_url: str) -> tuple[list[str], list[dict]]:
    """Text chunks (each headed with its file path) and their metadata. Config files are skipped."""
    texts, metadatas, splitters = [], [], {}
    for f in snapshot.files:
        if f.language == "Config":
            continue
        for chunk in _splitter(f.language, splitters).split_text(f.text):
            texts.append(f"File: {f.path}\n\n{chunk}")
            metadatas.append({"url": repo_url, "title": f"{repo_name}: {f.path}", "path": f.path,
                              "language": f.language, "source": "GitHub"})
            if len(texts) >= MAX_CHUNKS:
                return texts, metadatas
    return texts, metadatas


def index_repo(snapshot: RepoSnapshot, collection: str, repo_name: str, repo_url: str) -> int:
    """Blocking (embeds every chunk): run it in a worker thread. Returns the number of chunks."""
    texts, metadatas = chunk_repo(snapshot, repo_name, repo_url)
    if not texts:
        return 0
    ensure_collection(collection)
    get_vector_store(collection).add_texts(texts=texts, metadatas=metadatas)
    return len(texts)
