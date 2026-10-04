# robot-map

Spatial memory for a ROS 2 mobile robot: keyframe captioning with a small
vision-language model, semantic indexing, and natural-language query — all
on-device.

Designed for a Jetson AGX Orin running ROS 2 Kilted / JetPack 7.2.x, but
the AI side is pure Python and works anywhere a small VLM fits. Written
for the [`wheelbots`](https://github.com/Roboworks-Global/transbot) rosbot2
mini_akm but only needs `/image_raw` + `/tf` + a monocular camera.

## Concept

```
keyframe (image + robot pose)
  │
  ├─► VLM captions the scene              → text
  ├─► embedding model encodes the caption → vector
  └─► store {caption, vector, pose, ts,
             thumbnail path} in a local
             vector DB
        ▲
        │
Natural-language query:
   "which room did you last see the kettle in?"
        │
        ▼
   embed query → top-k similarity search → return {caption, pose, thumbnail}
```

## Runtime pieces

| Concern | Choice | Why |
|---|---|---|
| VLM | `Qwen/Qwen3-VL-2B-Instruct` (HF Transformers, bf16) | Small, no CUDA-graph power spikes |
| Embedder | `nomic-embed-text-v1.5` | Small, CPU-only, good retrieval quality |
| Vector DB | Chroma (sqlite backend) | Embedded, persistent, easy to inspect |
| Env | `uv` venv with system-site-packages | Reuses Jetson's torch/CUDA build |

## Install

Inside the wheelbots Lyrical container nothing needs installing: the package is built by colcon with the rest of the workspace and the venv below is mounted from the host (see `docs/docker_lyrical.md`). On the host:

```sh
uv venv --system-site-packages ~/.venvs/robot
source ~/.venvs/robot/bin/activate
uv pip install -e .
```

## Status

Early scaffolding. See git log for what's landed.
