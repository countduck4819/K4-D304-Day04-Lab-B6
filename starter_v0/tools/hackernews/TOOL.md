---
name: hackernews
track: team
kind: live_api
provider: HN Algolia
requires_env: []
inputs: [query, sort, limit]
outputs: [items]
side_effect: false
---
# hackernews

Search Hacker News stories via the Algolia API. Free, no key.

When to use vs other tools:
- Use `hackernews` when the user explicitly asks about Hacker News, "on HN", or
  the tech-community discussion of a topic.
- Use `lookup` for general web/news lookups.
- Use `social_search` for Twitter/X posts.

Arguments:
- `query` (optional): keyword to search stories. Empty query returns top stories.
- `sort` (default `top`): `top` for most upvoted matches, `new` for newest.
- `limit` (default `5`): how many stories to return, 1-20.

Returns `items` with `title`, `url`, `source`, and a `summary` line
("points · comments · by author").
