"""VLM-backed keyframe captioner.

Wraps Qwen3-VL-2B-Instruct via HF Transformers in eager mode (no CUDA-graph
capture, so the power draw stays smooth — important on Jetson Orin where
aggressive schedulers trip oc2/oc3 overcurrent throttling).

Usage as a library:

    from robot_memory.captioner import Captioner
    cap = Captioner()             # loads model on first call
    text = cap.caption("path/to/image.jpg")

Usage as a CLI:

    python -m robot_memory.captioner path/to/image.jpg
    robot-map-caption path/to/image.jpg     # after `pip install -e .`
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Optional, Union

from PIL import Image

DEFAULT_MODEL = "Qwen/Qwen3-VL-2B-Instruct"

DEFAULT_SYSTEM_PROMPT = (
    "You are the spatial memory of an indoor robot. "
    "For each image, produce ONE concise caption (<= 40 words) that captures: "
    "(1) the room type or area, (2) two or three notable objects, "
    "(3) any distinctive features that would help identify this exact spot again. "
    "Do not speculate about time of day, people, or anything not clearly visible."
)

DEFAULT_USER_PROMPT = "Describe this scene."


class Captioner:
    """Lazy-loaded VLM caption generator.

    The heavy model load happens on the first `caption()` call, not at
    construction, so import-time cost stays small (useful for tests that
    mock this class).
    """

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_new_tokens: int = 80,
        device: Optional[str] = None,
    ) -> None:
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.max_new_tokens = max_new_tokens
        self.device = device  # None => let accelerate pick via device_map="auto"
        self._model = None
        self._processor = None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        # Deferred import: torch / transformers are heavy and only needed
        # once we actually caption something.
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor

        device_map = self.device or "auto"
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

        self._processor = AutoProcessor.from_pretrained(
            self.model_id,
            trust_remote_code=True,
        )
        self._model = AutoModelForImageTextToText.from_pretrained(
            self.model_id,
            dtype=dtype,
            device_map=device_map,
            trust_remote_code=True,
        )
        self._model.eval()

    def caption(
        self,
        image: Union[str, Path, Image.Image],
        user_prompt: str = DEFAULT_USER_PROMPT,
    ) -> str:
        """Return a single-line caption for an image.

        `image` may be a file path or an already-loaded PIL Image.
        """
        self._ensure_loaded()
        import torch

        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": user_prompt},
                ],
            },
        ]

        # apply_chat_template handles both the text template and the image
        # placeholders for Qwen VL models.
        inputs = self._processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )
        inputs = {k: v.to(self._model.device) for k, v in inputs.items()}

        with torch.inference_mode():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
            )

        # Strip the prompt tokens so we only decode the assistant's reply.
        prompt_len = inputs["input_ids"].shape[1]
        new_tokens = output_ids[0, prompt_len:]
        text = self._processor.decode(new_tokens, skip_special_tokens=True)
        return text.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Caption an image with Qwen3-VL-2B.")
    parser.add_argument("image", type=Path, help="Path to a JPG/PNG file.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="HF model id.")
    parser.add_argument(
        "--max-new-tokens", type=int, default=80,
        help="Cap on generated tokens (default: 80).",
    )
    parser.add_argument(
        "--prompt", default=DEFAULT_USER_PROMPT,
        help="Override the user prompt.",
    )
    args = parser.parse_args()

    if not args.image.exists():
        parser.error(f"image not found: {args.image}")

    cap = Captioner(model_id=args.model, max_new_tokens=args.max_new_tokens)

    t0 = time.perf_counter()
    text = cap.caption(args.image, user_prompt=args.prompt)
    dt = time.perf_counter() - t0

    print(f"caption ({dt:.2f}s): {text}")


if __name__ == "__main__":
    main()
