from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err


WTTR_URL = "https://wttr.in/{location}"


def weather_now(location: str = "", units: str = "metric") -> dict[str, Any]:
    try:
        if not location.strip():
            raise ValueError("location is required")
        units = (units or "metric").lower()
        resp = requests.get(
            WTTR_URL.format(location=quote(location, safe="")),
            params={"format": "j1"},
            headers={"User-Agent": "day04-research-agent/1.0"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        current_list = data.get("current_condition") or []
        area_list = data.get("nearest_area") or []
        if not current_list:
            return {"tool": "weather_now", "location": location, "items": []}

        current = current_list[0]
        area_name = ""
        country = ""
        if area_list:
            area_name = ((area_list[0].get("areaName") or [{}])[0].get("value") or "").strip()
            country = ((area_list[0].get("country") or [{}])[0].get("value") or "").strip()

        temp = current.get("temp_C") if units == "metric" else current.get("temp_F")
        feels = current.get("FeelsLikeC") if units == "metric" else current.get("FeelsLikeF")
        unit_label = "C" if units == "metric" else "F"
        desc_list = current.get("weatherDesc") or []
        desc = (desc_list[0].get("value") if desc_list else "").strip()

        pretty_loc = ", ".join(x for x in [area_name, country] if x) or location
        summary = f"{desc}, {temp}°{unit_label} (feels {feels}°{unit_label}), humidity {current.get('humidity')}%, wind {current.get('windspeedKmph')} km/h"

        item = {
            "title": f"Weather in {pretty_loc}",
            "url": f"https://wttr.in/{quote(location, safe='')}",
            "source": "wttr.in",
            "summary": summary,
        }
        return {"tool": "weather_now", "location": location, "units": units, "items": [item]}
    except Exception as exc:
        return err("weather_now", exc)
