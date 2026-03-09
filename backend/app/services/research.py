"""Research service: FII/DII, News API, web scraping."""

from __future__ import annotations

import os
from typing import Any

import httpx


NSE_FII_DII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"
NSE_HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/reports/fii-dii",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def fetch_fii_dii(timeout: float = 10.0) -> list[dict[str, Any]]:
    """Fetch FII/DII trading activity from NSE. Returns [] on failure."""
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=NSE_HEADERS) as client:
            client.get("https://www.nseindia.com/reports/fii-dii")
            resp = client.get(NSE_FII_DII_URL)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return [{"type": "fii_dii", "data": d} for d in data]
            return [{"type": "fii_dii", "data": data}]
    except Exception:
        return []


def fetch_news_api(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Fetch news via NewsAPI.org. Requires NEWS_API_KEY in env."""
    api_key = os.environ.get("NEWS_API_KEY", "").strip()
    if not api_key:
        return []
    try:
        url = "https://newsapi.org/v2/everything"
        params = {"q": query, "apiKey": api_key, "pageSize": limit, "sortBy": "publishedAt"}
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("articles", [])[:limit]
            return [
                {
                    "type": "news",
                    "title": a.get("title", ""),
                    "source": a.get("source", {}).get("name", ""),
                    "publishedAt": a.get("publishedAt", ""),
                    "url": a.get("url", ""),
                    "description": a.get("description", "")[:200],
                }
                for a in articles
            ]
    except Exception:
        return []
