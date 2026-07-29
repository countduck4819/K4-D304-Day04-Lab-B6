from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err


RATES_URL = "https://open.er-api.com/v6/latest/{base}"


def currency_convert(amount: float = 1.0, base: str = "USD", target: str = "VND") -> dict[str, Any]:
    try:
        amount = float(amount if amount is not None else 1.0)
        base = (base or "USD").upper().strip()
        target = (target or "VND").upper().strip()
        if len(base) != 3 or len(target) != 3:
            raise ValueError("base and target must be 3-letter ISO currency codes")

        resp = requests.get(RATES_URL.format(base=base), timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if data.get("result") != "success":
            raise RuntimeError(data.get("error-type") or "rates api returned non-success")

        rates = data.get("rates") or {}
        if target not in rates:
            return {"tool": "currency_convert", "base": base, "target": target, "amount": amount, "items": []}

        rate = float(rates[target])
        converted = amount * rate
        as_of = data.get("time_last_update_utc") or ""

        item = {
            "title": f"{amount:g} {base} = {converted:,.2f} {target}",
            "url": "https://open.er-api.com/",
            "source": "open.er-api.com",
            "summary": f"1 {base} = {rate:g} {target} · updated {as_of}",
        }
        return {
            "tool": "currency_convert",
            "base": base,
            "target": target,
            "amount": amount,
            "rate": rate,
            "converted": converted,
            "items": [item],
        }
    except Exception as exc:
        return err("currency_convert", exc)
