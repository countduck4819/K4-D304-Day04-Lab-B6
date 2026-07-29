---
name: wiki
track: team
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [query, lang, sentences]
outputs: [items]
side_effect: false
---
# wiki

Fetches a concise summary of the top Wikipedia article matching `query`. Uses the
public MediaWiki `opensearch` endpoint to resolve the best title, then the REST
API `page/summary` endpoint to get an extract. No API key required.

When to use vs other tools:
- Use `wiki` for stable encyclopedic knowledge (definitions, biographies, concept
  overviews, historical facts).
- Use `lookup` for current events / news / open-web pages.
- Use `fetch` when the user gives an explicit URL.

Arguments:
- `query` (required): topic to look up.
- `lang` (default `en`): Wikipedia language edition, e.g. `en`, `vi`, `fr`.
- `sentences` (default `3`): number of sentences to keep from the extract.

Returns `items` with `title`, `url`, `source`, `summary`. Empty `items` when no
article matches.
