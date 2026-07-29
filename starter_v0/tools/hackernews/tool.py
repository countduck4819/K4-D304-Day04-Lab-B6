from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err


HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
HN_FRONT_URL = "https://hn.algolia.com/api/v1/search"


def hn_search(query: str = "", sort: str = "top", limit: int = 5) -> dict[str, Any]:
    try:
        limit = max(1, min(int(limit or 5), 20))
        sort = (sort or "top").lower()
        params: dict[str, Any] = {
            "tags": "story",
            "hitsPerPage": limit,
        }
        if query.strip():
            params["query"] = query
        if sort == "new":
            params["tags"] = "story"
            params["numericFilters"] = ""
            endpoint = "https://hn.algolia.com/api/v1/search_by_date"
        else:
            endpoint = HN_SEARCH_URL

        resp = requests.get(endpoint, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        items = []
        for hit in data.get("hits", [])[:limit]:
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            items.append({
                "title": hit.get("title") or hit.get("story_title") or "",
                "url": url,
                "source": domain(url),
                "summary": f"{hit.get('points', 0)} points · {hit.get('num_comments', 0)} comments · by {hit.get('author', 'unknown')}",
            })
        return {"tool": "hn_search", "query": query, "sort": sort, "items": items}
    except Exception as exc:
        return err("hn_search", exc)
