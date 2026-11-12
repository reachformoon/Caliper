#!/usr/bin/env python
"""Download the embedding model (mirror-friendly).

Usage: python scripts/fetch_model.py
"""
from __future__ import annotations

import os

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

MODEL = "BAAI/bge-small-zh-v1.5"


def main() -> None:
    from fastembed import TextEmbedding

    model = TextEmbedding(model_name=MODEL)
    vec = list(model.embed(["测试中文向量"]))[0]
    print(f"model ok: {MODEL}, dim={len(vec)}")


if __name__ == "__main__":
    main()
