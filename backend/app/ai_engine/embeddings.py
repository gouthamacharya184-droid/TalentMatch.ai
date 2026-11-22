import os
import re
import math
import logging
import hashlib
from typing import List, Optional, Dict
from collections import Counter
import numpy as np
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Embedding service providing semantic vectors and cosine similarity.
    Supports 3 resilient tiers:
      Tier 1: Local Sentence Transformers (all-MiniLM-L6-v2, 384-D) with LRU caching
      Tier 2: Google Gemini Embeddings API (text-embedding-004, 768-D) for serverless execution
      Tier 3: High-accuracy Pure-Python / Scikit-Learn TF-IDF N-gram cosine similarity (deterministic fallback)
    """

    _instance = None
    _model = None
    _use_transformers = True
    _embedding_cache: Dict[str, np.ndarray] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._embedding_cache = {}
            cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self):
        """Attempt to load SentenceTransformers model."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            try:
                # Fast path: load instantly from local cache if already present
                self._model = SentenceTransformer(settings.EMBEDDING_MODEL, local_files_only=True)
            except Exception:
                # Fallback to online fetch if not cached yet
                self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            self._use_transformers = True
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.info(
                f"SentenceTransformer not loaded ({str(e)}). "
                "Active semantic modes: Google Gemini API embeddings + Deterministic TF-IDF."
            )
            self._model = None
            self._use_transformers = False

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Retrieve embedding from cache or encode using SentenceTransformers."""
        if not self._use_transformers or self._model is None:
            return None
        text_hash = hashlib.sha256(f"st_{text}".encode("utf-8")).hexdigest()
        if text_hash in self._embedding_cache:
            return self._embedding_cache[text_hash]

        try:
            emb = self._model.encode([text], convert_to_numpy=True)[0]
            if len(self._embedding_cache) >= 5000:
                self._embedding_cache.pop(next(iter(self._embedding_cache)))
            self._embedding_cache[text_hash] = emb
            return emb
        except Exception as e:
            logger.warning(f"Transformer encoding failed: {e}")
            return None

    def _get_gemini_embedding(self, text: str) -> Optional[np.ndarray]:
        """Fetch high-precision 768-D semantic vector from Google Gemini API."""
        api_key = getattr(settings, "LLM_API_KEY", "") or os.environ.get("LLM_API_KEY", "")
        if not api_key or not api_key.strip() or api_key.strip() == "PASTE_YOUR_API_KEY_HERE":
            return None

        text_hash = hashlib.sha256(f"gemini_{text}".encode("utf-8")).hexdigest()
        if text_hash in self._embedding_cache:
            return self._embedding_cache[text_hash]

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key.strip()}"
            payload = {
                "model": "models/text-embedding-004",
                "content": {
                    "parts": [{"text": text[:2048]}]
                }
            }
            with httpx.Client(timeout=4.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    values = data.get("embedding", {}).get("values", [])
                    if values:
                        emb = np.array(values, dtype=np.float32)
                        norm = np.linalg.norm(emb)
                        if norm > 0:
                            emb = emb / norm
                        if len(self._embedding_cache) >= 5000:
                            self._embedding_cache.pop(next(iter(self._embedding_cache)))
                        self._embedding_cache[text_hash] = emb
                        return emb
        except Exception as e:
            logger.debug(f"Gemini embedding API call skipped: {e}")
            return None
        return None

    @staticmethod
    def _pure_tfidf_similarity(text_a: str, text_b: str) -> float:
        """
        Pure-Python n-gram TF-IDF cosine similarity.
        Implements exact smooth-IDF formulation identical to Scikit-Learn without requiring heavy binary dependencies.
        """
        def extract_tokens(text: str):
            words = re.findall(r"\b[a-zA-Z0-9_+#.-]+\b", text.lower())
            unigrams = [w for w in words if len(w) > 1]
            bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
            return unigrams + bigrams

        tokens_a = extract_tokens(text_a)
        tokens_b = extract_tokens(text_b)
        if not tokens_a or not tokens_b:
            return 0.0

        counts_a = Counter(tokens_a)
        counts_b = Counter(tokens_b)
        all_terms = set(counts_a.keys()).union(set(counts_b.keys()))

        dot_prod = 0.0
        norm_a = 0.0
        norm_b = 0.0

        for term in all_terms:
            df = (1 if term in counts_a else 0) + (1 if term in counts_b else 0)
            idf = math.log(3.0 / (df + 1.0)) + 1.0  # Smooth IDF: log((N+1)/(df+1)) + 1
            v_a = counts_a.get(term, 0) * idf
            v_b = counts_b.get(term, 0) * idf
            dot_prod += v_a * v_b
            norm_a += v_a * v_a
            norm_b += v_b * v_b

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        sim = float(dot_prod / (math.sqrt(norm_a) * math.sqrt(norm_b)))
        return round(max(0.0, min(1.0, sim)), 4)

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """
        Compute semantic cosine similarity score between two texts in range [0.0, 1.0].
        """
        if not text_a or not text_b:
            return 0.0

        if text_a.strip().lower() == text_b.strip().lower():
            return 1.0

        # Method 1: Sentence Transformers with Cached Embeddings (Local/GPU)
        if self._use_transformers and self._model is not None:
            emb_a = self._get_embedding(text_a)
            emb_b = self._get_embedding(text_b)
            if emb_a is not None and emb_b is not None:
                try:
                    from sklearn.metrics.pairwise import cosine_similarity
                    sim = float(cosine_similarity(emb_a.reshape(1, -1), emb_b.reshape(1, -1))[0][0])
                    normalized = max(0.0, min(1.0, (sim + 1.0) / 2.0))
                    return round(normalized, 4)
                except Exception:
                    # Fallback to pure numpy dot product
                    sim = float(np.dot(emb_a, emb_b) / (np.linalg.norm(emb_a) * np.linalg.norm(emb_b)))
                    normalized = max(0.0, min(1.0, (sim + 1.0) / 2.0))
                    return round(normalized, 4)

        # Method 2: Google Gemini Embeddings API (Serverless Cloud, 768-D)
        g_emb_a = self._get_gemini_embedding(text_a)
        if g_emb_a is not None:
            g_emb_b = self._get_gemini_embedding(text_b)
            if g_emb_b is not None:
                try:
                    sim = float(np.dot(g_emb_a, g_emb_b))
                    normalized = max(0.0, min(1.0, (sim + 1.0) / 2.0))
                    return round(normalized, 4)
                except Exception as e:
                    logger.warning(f"Gemini API cosine similarity failed: {e}")

        # Method 3: Deterministic Mathematical TF-IDF Cosine Similarity Fallback
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
            sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
            return round(max(0.0, min(1.0, sim)), 4)
        except Exception:
            return self._pure_tfidf_similarity(text_a, text_b)

    def compute_batch_similarity(self, query: str, documents: List[str]) -> List[float]:
        """Compute cosine similarity between one query and multiple documents."""
        if not documents:
            return []
        return [self.compute_similarity(query, doc) for doc in documents]

    def get_model_info(self) -> dict:
        """Returns details about the actively loaded semantic embedding model."""
        if self._use_transformers and self._model is not None:
            return {
                "model_name": settings.EMBEDDING_MODEL,
                "is_transformer": True,
                "engine": "Sentence Transformers (all-MiniLM-L6-v2)",
                "embedding_dimension": 384,
                "status": "active"
            }
        api_key = getattr(settings, "LLM_API_KEY", "") or os.environ.get("LLM_API_KEY", "")
        if api_key and api_key.strip() != "PASTE_YOUR_API_KEY_HERE":
            return {
                "model_name": "Google Gemini (text-embedding-004)",
                "is_transformer": True,
                "engine": "Gemini Embeddings API",
                "embedding_dimension": 768,
                "status": "active_cloud"
            }
        return {
            "model_name": "TF-IDF N-Gram Vectorizer (Deterministic)",
            "is_transformer": False,
            "engine": "Deterministic TF-IDF",
            "embedding_dimension": None,
            "status": "fallback"
        }
