"""Chroma-backed keyframe store.

Persists {caption, embedding, pose, timestamp, thumbnail_path} tuples
keyed by an opaque keyframe_id, and lets you query the top-k semantic
matches for a given embedding vector.

Usage:

    from robot_memory.store import Store, Keyframe
    store = Store()
    store.add(Keyframe(
        caption="kitchen with a stainless steel fridge",
        embedding=vec_from_embedder,
        pose_xy=(3.0, 2.0),
        pose_yaw=1.57,
    ))
    hits = store.search(query_vec, k=5)
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Union

import numpy as np

DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "robot-map" / "chroma_db"
DEFAULT_COLLECTION = "keyframes"


@dataclass
class Keyframe:
    """One captioned keyframe + its metadata."""

    caption: str
    embedding: Union[np.ndarray, Sequence[float]]
    pose_xy: tuple = (0.0, 0.0)
    pose_yaw: float = 0.0
    timestamp: float = field(default_factory=time.time)
    thumbnail_path: Optional[str] = None
    keyframe_id: str = field(default_factory=lambda: uuid.uuid4().hex)


class Store:
    """Persistent Chroma collection with cosine distance.

    Instantiation is cheap; the underlying Chroma client and collection
    open lazily on the first `add()` / `search()` / `count()` call.
    """

    def __init__(
        self,
        db_path: Union[str, Path] = DEFAULT_DB_PATH,
        collection: str = DEFAULT_COLLECTION,
    ) -> None:
        self.db_path = Path(db_path)
        self.collection_name = collection
        self._client = None
        self._collection = None

    def _ensure_open(self) -> None:
        if self._collection is not None:
            return
        import chromadb

        self.db_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self.db_path))
        # cosine matches the L2-normalized nomic embeddings.
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _to_list(embedding) -> List[float]:
        if isinstance(embedding, np.ndarray):
            return embedding.astype(np.float32).ravel().tolist()
        return list(embedding)

    def add(self, kf: Keyframe) -> None:
        """Insert a keyframe. Overwrites if the id already exists."""
        self._ensure_open()
        self._collection.upsert(
            ids=[kf.keyframe_id],
            embeddings=[self._to_list(kf.embedding)],
            documents=[kf.caption],
            metadatas=[{
                "pose_x": float(kf.pose_xy[0]),
                "pose_y": float(kf.pose_xy[1]),
                "pose_yaw": float(kf.pose_yaw),
                "timestamp": float(kf.timestamp),
                "thumbnail_path": kf.thumbnail_path or "",
            }],
        )

    def search(self, query_embedding, k: int = 5) -> List[dict]:
        """Return top-k hits ordered by ascending cosine distance.

        Each hit is a dict:
            {id, caption, distance, metadata: {pose_x, pose_y, pose_yaw,
                                              timestamp, thumbnail_path}}
        """
        self._ensure_open()
        results = self._collection.query(
            query_embeddings=[self._to_list(query_embedding)],
            n_results=k,
        )

        # Chroma nests everything under an outer list of query batches.
        hits: List[dict] = []
        if not results["ids"] or not results["ids"][0]:
            return hits
        for i in range(len(results["ids"][0])):
            hits.append({
                "id": results["ids"][0][i],
                "caption": results["documents"][0][i],
                "distance": results["distances"][0][i],
                "metadata": results["metadatas"][0][i] or {},
            })
        return hits

    def count(self) -> int:
        self._ensure_open()
        return self._collection.count()

    def reset(self) -> None:
        """Drop and recreate the collection. Destructive."""
        self._ensure_open()
        self._client.delete_collection(self.collection_name)
        self._collection = None
        self._ensure_open()
