from __future__ import annotations

from typing import Any

import httpx


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "llama3.2", embed_model: str = "nomic-embed-text") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.embed_model = embed_model

    async def generate(self, prompt: str, model: str | None = None) -> str:
        payload = {"model": model or self.model, "prompt": prompt, "stream": False}
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
        return str(data.get("response", ""))

    async def embed(self, text: str, model: str | None = None) -> list[float]:
        payload = {"model": model or self.embed_model, "input": text}
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/api/embed", json=payload)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
        embeddings = data.get("embeddings", [])
        if not embeddings:
            return []
        first = embeddings[0]
        if isinstance(first, list):
            return [float(x) for x in first]
        return []
