---
name: currency
track: team
kind: live_api
provider: open.er-api.com
requires_env: []
inputs: [amount, base, target]
outputs: [items]
side_effect: false
---
# currency

Convert an amount between two fiat currencies at the latest published mid-market
rate. Free, no key.

When to use vs other tools:
- Use `currency` when the user asks to convert between currencies or wants the
  current rate of one currency against another.
- Do NOT use for crypto prices (BTC/ETH) — this endpoint is fiat only.
- Do NOT use for historical rates on a specific past date.

Arguments:
- `amount` (default `1.0`): amount to convert in the base currency.
- `base` (default `USD`): 3-letter ISO code of the source currency.
- `target` (default `VND`): 3-letter ISO code of the target currency.

Returns a single `items` entry with the converted amount and the applied rate.
