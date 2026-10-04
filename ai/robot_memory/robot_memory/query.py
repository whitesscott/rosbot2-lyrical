"""CLI for querying the spatial memory.

    robot-map-query "where is the fridge?"

Prints the top-k hits with distance, pose, and caption.
"""

from __future__ import annotations

import argparse
import sys

from robot_memory.embedder import Embedder
from robot_memory.store import Store


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the robot's spatial memory.")
    parser.add_argument("query", help="Natural-language query.")
    parser.add_argument("-k", "--top-k", type=int, default=5, help="Results to show (default: 5).")
    parser.add_argument(
        "--db-path", default=None,
        help="Chroma DB path (default: ~/.local/share/robot-map/chroma_db)."
    )
    parser.add_argument(
        "--collection", default="keyframes",
        help="Chroma collection name (default: keyframes)."
    )
    args = parser.parse_args()

    embedder = Embedder()
    store_kwargs = {"collection": args.collection}
    if args.db_path:
        store_kwargs["db_path"] = args.db_path
    store = Store(**store_kwargs)

    total = store.count()
    if total == 0:
        print("(store is empty — no keyframes have been added yet)", file=sys.stderr)
        sys.exit(1)

    q_vec = embedder.encode(args.query, is_query=True)[0]
    hits = store.search(q_vec, k=args.top_k)

    print(f"query: {args.query!r}   store: {total} keyframes")
    print("-" * 72)
    for rank, hit in enumerate(hits, 1):
        md = hit["metadata"]
        pose = f"({md.get('pose_x', 0.0):.2f}, {md.get('pose_y', 0.0):.2f}) yaw={md.get('pose_yaw', 0.0):.2f}"
        print(f"[{rank}] dist={hit['distance']:.3f}   pose={pose}")
        print(f"    {hit['caption']}")
        thumb = md.get("thumbnail_path")
        if thumb:
            print(f"    thumb: {thumb}")
        print()


if __name__ == "__main__":
    main()
