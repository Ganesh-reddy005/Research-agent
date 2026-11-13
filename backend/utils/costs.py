"""What LLM calls cost, from OpenRouter's public price list (fetched once per process, free to call)."""
import time
import httpx

PRICES_URL = "https://openrouter.ai/api/v1/models"
REFRESH_SECONDS = 24 * 3600
_prices: dict[str, tuple[float, float]] = {}  # model id -> (dollars per input token, per output token)
_fetched_at = 0.0


def _load_prices() -> None:
    global _fetched_at
    if _prices and time.monotonic() - _fetched_at < REFRESH_SECONDS:
        return
    try:
        models = httpx.get(PRICES_URL, timeout=15).json().get("data", [])
    except (httpx.HTTPError, ValueError):
        return  # unknown prices: costs read as 0 rather than failing the run
    for model in models:
        pricing = model.get("pricing") or {}
        try:
            _prices[model["id"]] = (float(pricing.get("prompt", 0)), float(pricing.get("completion", 0)))
        except (TypeError, ValueError, KeyError):
            continue
    _fetched_at = time.monotonic()


def cost_usd(usage: dict) -> float:
    """usage: {model name: {"input_tokens", "output_tokens"}}, as LangChain's usage callback reports it."""
    _load_prices()
    total = 0.0
    for model, counts in usage.items():
        prompt, completion = _prices.get(model, _prices.get(model.split(":")[-1], (0.0, 0.0)))
        total += counts.get("input_tokens", 0) * prompt + counts.get("output_tokens", 0) * completion
    return round(total, 4)


def tokens(usage: dict) -> int:
    return sum(c.get("input_tokens", 0) + c.get("output_tokens", 0) for c in usage.values())
