---
name: weather
track: team
kind: live_api
provider: wttr.in
requires_env: []
inputs: [location, units]
outputs: [items]
side_effect: false
---
# weather

Get the current weather condition for a location via wttr.in. Free, no key.

When to use vs other tools:
- Use `weather` when the user asks about weather, temperature, or conditions for
  a specific city/place right now.
- Do NOT use for weather forecasts more than a day out (wttr.in is best for
  current conditions) or for historical weather.

Arguments:
- `location` (required): city, "City, Country", airport code, or coordinates.
- `units` (default `metric`): `metric` for Celsius/km-h, `imperial` for Fahrenheit.

Returns a single `items` entry with a summary line describing conditions,
temperature, feels-like, humidity, and wind.
