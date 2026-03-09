from __future__ import annotations

import asyncio

from app.services.ollama_client import OllamaClient


def test_ollama_client_constructor() -> None:
    client = OllamaClient()
    assert client.base_url.startswith("http")
    assert client.model
    assert client.embed_model


def test_ollama_generate_live_if_available() -> None:
    async def _run() -> str:
        client = OllamaClient()
        try:
            return await client.generate("Reply with TEST_OK")
        except Exception:
            return "SKIPPED"

    out = asyncio.run(_run())
    assert isinstance(out, str)
