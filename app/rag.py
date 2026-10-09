"""
RAG pipeline for the CCA AI Assistant.

Pipeline
--------
Ingestion : load file -> split into chunks (page-aware) -> store in DB
Question  : clean query -> expand keywords -> keyword filter (SQL)
            -> BM25 ranking -> top-k chunks -> prompt + context -> Gemini
            -> answer + page-level citations

Drop-in replacement: same class name, constructor, and return keys that
app/main.py already expects.
"""

import math
import os
import re
from typing import Any, Dict, List, Optional

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import or_

from app.database import Chunk, Database, Document

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

NO_ANSWER_TEXT = "The provided context does not contain information regarding this topic."

# Phrases that tell us the LLM refused to answer (used for is_supported).
REFUSAL_MARKERS = [
    "does not contain",
    "do not contain",
    "not provided",
    "not mentioned",
    "no information",
    "cannot be found",
    "not explicitly",
]

# Words that carry no meaning for search. Without this list, words such as
# "what" or "must" match almost every chunk and ruin the ranking.
STOPWORDS = {
    "about", "above", "after", "again", "against", "all", "also", "and", "any", "are", "because",
    "been", "before", "being", "below", "between", "both", "but", "can", "could",
    "did", "does", "doing", "done", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "her", "here", "him", "his", "how",
    "into", "its", "just", "more", "most", "must", "need", "not", "now", "off",
    "once", "only", "other", "our", "out", "over", "own", "per", "same", "shall",
    "she", "should", "some", "such", "than", "that", "the", "their", "them", "then",
    "there", "these", "they", "this", "those", "through", "too", "under", "until",
    "very", "was", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "will", "with", "would", "you", "your", "yours", "regarding", "strictly",
    "immediate", "following", "provide", "provided", "include", "including", "tell",
    "explain", "describe", "give", "please", "many", "much", "get", "use", "used",
}

# Small synonym map: query term (stem) -> extra terms worth searching for.
# Extend this for your own handbook vocabulary.
EXPANSIONS = {
    "medical": ["health", "doctor", "wellbeing"],
    "emergenc": ["urgent", "safety", "evacuat"],
    "fire": ["alarm", "evacuat", "assembly"],
    "alarm": ["fire", "evacuat"],
    "guest": ["visitor", "overnight"],
    "visitor": ["guest", "overnight"],
    "fee": ["payment", "invoice", "deposit"],
    "payment": ["fee", "invoice", "deposit"],
    "repair": ["maintenance", "fault"],
    "maintenance": ["repair", "fault"],
    "waste": ["recycl", "rubbish", "bin"],
    "recycl": ["waste", "rubbish", "bin"],
    "internet": ["wifi", "wi-fi", "broadband"],
    "wifi": ["internet", "broadband"],
    "pest": ["bed bug", "infestation"],
    "post": ["mail", "parcel", "package", "deliver"],
    "parcel": ["post", "package", "deliver"],
    "bring": ["pack", "provided"],
}

# BM25 parameters (standard values).
BM25_K1 = 1.5
BM25_B = 0.75

# Chunks on pages before this one are ignored (e.g. cover / table of contents).
# Page numbers are 1-based, as in a PDF viewer. Default 1 = ignore nothing.
MIN_CONTENT_PAGE = int(os.getenv("MIN_CONTENT_PAGE", "1"))

# Max chunks pulled from the DB for ranking.
MAX_CANDIDATES = 500


# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------

def _stem(word: str) -> str:
    """Very light stemmer so 'vaccinations' matches 'vaccination'."""
    for suffix in ("ations", "ation", "ings", "ing", "ies", "es", "ed", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def extract_keywords(question: str) -> List[str]:
    """Lower-case, strip punctuation, drop stopwords, stem, remove duplicates."""
    tokens = re.findall(r"[a-z0-9]+", question.lower())
    keywords: List[str] = []
    for tok in tokens:
        if len(tok) < 3 or tok in STOPWORDS:
            continue
        stem = _stem(tok)
        if stem not in keywords:
            keywords.append(stem)
    return keywords


def expand_keywords(keywords: List[str]) -> List[str]:
    """Add synonyms from EXPANSIONS (query optimisation)."""
    expanded = list(keywords)
    for kw in keywords:
        for extra in EXPANSIONS.get(kw, []):
            if extra not in expanded:
                expanded.append(extra)
    return expanded


def _response_text(response: Any) -> str:
    """Newer LangChain Gemini versions can return a list of content blocks."""
    content = getattr(response, "content", response)
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        return "".join(parts).strip()
    return str(content).strip()


# --------------------------------------------------------------------------
# RAG pipeline
# --------------------------------------------------------------------------

class RAGPipeline:
    def __init__(
        self,
        GEMINI_API_KEY: str,
        model: str = "gemini-2.5-flash",
        embedding_model: str = "text-embedding-004",  # kept for compatibility, unused
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.GEMINI_API_KEY = GEMINI_API_KEY
        self.db = Database()

        # Chunking: tries paragraph -> line -> sentence -> word boundaries.
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        # Generation model (temperature 0 = consistent, grounded answers).
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=0,
            google_api_key=GEMINI_API_KEY,
        )

    # ------------------------------------------------------------------
    # Ingestion: load -> chunk -> store
    # ------------------------------------------------------------------

    def _load_documents(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return PyPDFLoader(file_path).load()
        if ext in (".txt", ".md"):
            return TextLoader(file_path, encoding="utf-8").load()
        if ext in (".docx", ".doc"):
            try:
                from langchain_community.document_loaders import Docx2txtLoader
                return Docx2txtLoader(file_path).load()
            except ImportError as exc:
                raise ValueError("Word files need: pip install docx2txt") from exc
        raise ValueError(f"Unsupported file type: {ext}")

    def _remove_existing(self, filename: str) -> None:
        """Re-uploading a file replaces the old copy instead of duplicating it."""
        session = self.db.get_session()
        try:
            for doc in session.query(Document).filter(Document.title == filename).all():
                session.delete(doc)  # cascade removes its chunks
            session.commit()
        finally:
            session.close()

    def ingest_document(self, file_path: str) -> Dict[str, Any]:
        """Load, chunk, and store a document."""
        filename = os.path.basename(file_path)

        raw_docs = self._load_documents(file_path)
        split_docs = self.text_splitter.split_documents(raw_docs)

        self._remove_existing(filename)
        doc_id = self.db.add_document(
            title=filename,
            source_type=filename.rsplit(".", 1)[-1].lower(),
            file_path=file_path,
        )

        chunks_data = []
        for idx, doc in enumerate(split_docs):
            text = doc.page_content.strip()
            if not text:
                continue
            # PyPDFLoader pages are 0-based; store 1-based to match a PDF viewer.
            page = int(doc.metadata.get("page", 0)) + 1
            chunks_data.append(
                {
                    "text": text,
                    "page": page,
                    "chunk_index": idx,
                    "metadata": {"source": filename, "page": page},
                }
            )

        self.db.add_chunks(doc_id, chunks_data)

        return {
            "document_id": doc_id,
            "filename": filename,
            "chunks_created": len(chunks_data),
        }

    # ------------------------------------------------------------------
    # Retrieval: keyword filter -> BM25 ranking
    # ------------------------------------------------------------------

    def _retrieve(self, session, keywords: List[str], top_k: int):
        """Return (ranked_chunks, scores, matched_keywords)."""
        if not keywords:
            return [], [], set()

        base = session.query(Chunk).filter(Chunk.page >= MIN_CONTENT_PAGE)

        # 1) SQL pre-filter: chunk must contain at least one keyword.
        match_filter = or_(*[Chunk.text.ilike(f"%{kw}%") for kw in keywords])
        candidates = base.filter(match_filter).limit(MAX_CANDIDATES).all()
        if not candidates:
            return [], [], set()

        # 2) Document frequency of each keyword (for the IDF weight).
        total_chunks = max(base.count(), 1)
        doc_freq = {
            kw: base.filter(Chunk.text.ilike(f"%{kw}%")).count() for kw in keywords
        }

        # 3) BM25 score for every candidate.
        lengths = [len(c.text.split()) for c in candidates]
        avg_len = sum(lengths) / len(lengths) or 1.0

        scored = []
        for chunk, length in zip(candidates, lengths):
            text = chunk.text.lower()
            score = 0.0
            for kw in keywords:
                tf = text.count(kw)
                if tf == 0:
                    continue
                df = doc_freq.get(kw, 0)
                idf = math.log(1 + (total_chunks - df + 0.5) / (df + 0.5))
                norm = tf + BM25_K1 * (1 - BM25_B + BM25_B * length / avg_len)
                score += idf * (tf * (BM25_K1 + 1)) / norm
            scored.append((score, chunk))

        # 4) Highest score first, then keep top_k.
        scored.sort(key=lambda pair: pair[0], reverse=True)
        top = scored[:top_k]

        chunks = [c for _, c in top]
        scores = [s for s, _ in top]
        matched = {kw for c in chunks for kw in keywords if kw in c.text.lower()}
        return chunks, scores, matched

    # ------------------------------------------------------------------
    # Question answering
    # ------------------------------------------------------------------

    def answer_question(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Retrieve the best chunks and generate a grounded answer with citations."""
        session = self.db.get_session()
        try:
            base_keywords = extract_keywords(question)
            keywords = expand_keywords(base_keywords)
            chunks, scores, matched = self._retrieve(session, keywords, top_k)

            # Nothing relevant found: do not guess and do not waste an LLM call.
            if not chunks:
                return {
                    "answer": NO_ANSWER_TEXT,
                    "citations": [],
                    "confidence_score": 0.0,
                    "is_supported": False,
                }

            # ---- Prompt + context (each chunk is labelled with its source) ----
            context = "\n\n".join(
                f"[Source: {c.document.title if c.document else 'Document'}, page {c.page}]\n{c.text}"
                for c in chunks
            )
            prompt = (
                "You are a helpful university accommodation assistant.\n"
                "Answer the question using ONLY the context below.\n"
                "Rules:\n"
                "- Use every relevant detail in the context; give a complete answer.\n"
                "- Mention the page number(s) your answer comes from, like (page 12).\n"
                f"- If the context does not contain the answer, reply exactly: '{NO_ANSWER_TEXT}'\n"
                "- If it only partly answers, give the part you can and state what is missing.\n"
                "- Never guess or add outside information.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {question}\n\nAnswer:"
            )

            # ---- LLM response ----
            answer = _response_text(self.llm.invoke(prompt))

            # ---- Citations with real relevance scores (0-1, relative to best) ----
            best = max(scores) or 1.0
            citations = [
                {
                    "document_title": c.document.title if c.document else "Document",
                    "page": c.page,
                    "chunk_text": c.text,
                    "chunk_index": c.chunk_index,
                    "relevance_score": round(s / best, 3),
                }
                for c, s in zip(chunks, scores)
            ]

            # ---- Honest support / confidence ----
            refused = any(marker in answer.lower() for marker in REFUSAL_MARKERS)
            is_supported = not refused
            # Confidence = share of query terms found in the retrieved chunks.
            coverage = len(matched) / len(keywords) if keywords else 0.0
            confidence = round(coverage, 2) if is_supported else 0.0

            result = {
                "answer": answer,
                "citations": citations if is_supported else citations[:1],
                "confidence_score": confidence,
                "is_supported": is_supported,
            }

            # ---- Save chat history (never break the request if this fails) ----
            try:
                self.db.add_chat_history(question, answer, result["citations"])
            except Exception:
                pass

            return result
        finally:
            session.close()
