from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, domain, err


WIKI_SEARCH_URL = "https://{lang}.wikipedia.org/w/api.php"
WIKI_SUMMARY_URL = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"


def wiki_lookup(query: str = "", lang: str = "en", sentences: int = 3) -> dict[str, Any]:
    try:
        if not query.strip():
            raise ValueError("query is required")
        lang = (lang or "en").lower()

        search_resp = requests.get(
            WIKI_SEARCH_URL.format(lang=lang),
            params={
                "action": "opensearch",
                "search": query,
                "limit": 1,
                "namespace": 0,
                "format": "json",
            },
            headers={"User-Agent": "day04-research-agent/1.0"},
            timeout=TIMEOUT,
        )
        search_resp.raise_for_status()
        data = search_resp.json()

        titles = data[1] if len(data) > 1 else []
        urls = data[3] if len(data) > 3 else []
        if not titles:
            return {"tool": "wiki_lookup", "query": query, "lang": lang, "items": []}

        title = titles[0]
        page_url = urls[0] if urls else ""

        summary_resp = requests.get(
            WIKI_SUMMARY_URL.format(lang=lang, title=quote(title, safe="")),
            headers={"User-Agent": "day04-research-agent/1.0"},
            timeout=TIMEOUT,
        )
        summary_resp.raise_for_status()
        summary_data = summary_resp.json()

        extract = summary_data.get("extract") or ""
        parts = [s.strip() for s in extract.split(". ") if s.strip()]
        limit = max(1, int(sentences or 3))
        trimmed = ". ".join(parts[:limit])
        if trimmed and not trimmed.endswith("."):
            trimmed += "."

        item = {
            "title": summary_data.get("title") or title,
            "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page") or page_url,
            "source": domain(page_url or "wikipedia.org"),
            "summary": trimmed,
        }
        return {"tool": "wiki_lookup", "query": query, "lang": lang, "items": [item]}
    except Exception as exc:
        return err("wiki_lookup", exc)
