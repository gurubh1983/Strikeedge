"""MoneyControl-style news scraper for sentiment analysis."""

from __future__ import annotations

from typing import Any

import httpx
from bs4 import BeautifulSoup


MONEYCONTROL_NIFTY_URL = "https://www.moneycontrol.com/news/business/markets/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def scrape_moneycontrol_headlines(underlying: str = "NIFTY", limit: int = 10) -> list[dict[str, Any]]:
    """Scrape market headlines from MoneyControl. Returns title, link, snippet."""
    headlines: list[dict[str, Any]] = []
    try:
        url = MONEYCONTROL_NIFTY_URL if "NIFTY" in underlying.upper() else "https://www.moneycontrol.com/news/business/"
        with httpx.Client(timeout=15.0, follow_redirects=True, headers=HEADERS) as client:
            resp = client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.select("a[href*='/news/']")[:limit * 2]:
                title = (a.get_text() or "").strip()
                href = a.get("href", "")
                if title and len(title) > 15 and href and "/news/" in href:
                    headlines.append({"title": title[:200], "url": href})
                    if len(headlines) >= limit:
                        break
    except Exception:
        pass
    return headlines[:limit]
