"""Text embedder for keyframe captions.

Default model: `BAAI/bge-small-en-v1.5` — 33M params, 384-dim, ~130 MB,
runs happily on CPU, native transformers (no `trust_remote_code`), stays
compatible with transformers 5.x. Good retrieval quality for short
caption-style documents.

Some embedders (BGE-large, E5, nomic) use task-specific prefixes to bias
the vectors for symmetric-vs-asymmetric retrieval. This wrapper exposes
`doc_prefix` and `query_prefix` so callers can swap in a prefix-aware
model without changing the interface. BGE-small does not need prefixes
in practice (BAAI notes prefixing helps only marginally on the small
variant), so the defaults are empty strings.

Usage:

    from robot_memory.embedder import Embedder
    e = Embedder()
    doc_vec = e.encode("living room with a couch")           # for storage
    q_vec = e.encode("where is the couch?", is_query=True)   # for search
"""

from __future__ import annotations

from typing import Sequence, Union

import numpy as np

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"


class Embedder:
    """Lazy-loaded sentence-transformers embedder.

    The model is not loaded until the first `encode()` call, keeping
    import cost small so tests that mock this class stay fast.
    """

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL,
        doc_prefix: str = "",
        query_prefix: str = "",
    ) -> None:
        self.model_id = model_id
        self.doc_prefix = doc_prefix
        self.query_prefix = query_prefix
        self._model = None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.model_id)

    def encode(
        self,
        texts: Union[str, Sequence[str]],
        is_query: bool = False,
    ) -> np.ndarray:
        """Return a (N, dim) numpy array of L2-normalized embeddings.

        `texts` may be a single string or an iterable of strings. The
        result always has shape (N, dim) so callers can index
        consistently.
        """
        self._ensure_loaded()

        if isinstance(texts, str):
            texts = [texts]
        else:
            texts = list(texts)

        prefix = self.query_prefix if is_query else self.doc_prefix
        if prefix:
            texts = [f"{prefix}{t}" for t in texts]

        vecs = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        if vecs.ndim == 1:
            vecs = vecs.reshape(1, -1)
        return vecs

    @property
    def dim(self) -> int:
        """Embedding dimension (384 for bge-small-en-v1.5)."""
        self._ensure_loaded()
        # `get_embedding_dimension` is the new name in sentence-transformers 3.x;
        # fall back to the old name for older installs.
        getter = getattr(
            self._model,
            "get_embedding_dimension",
            self._model.get_sentence_embedding_dimension,
        )
        return getter()
