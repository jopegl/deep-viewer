import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache

ROR_URL = "https://api.ror.org/v2/organizations"


def _display_name(item):
    for name in item.get("names", []):
        if "ror_display" in name.get("types", []):
            return name["value"]
    return None


def _country(item):
    locations = item.get("locations") or []
    if not locations:
        return ""
    return locations[0].get("geonames_details", {}).get("country_name", "")


def search_institutions(query, limit=10):
    query = query.strip()
    if len(query) < 3:
        return []

    key = f"ror:{query.lower()}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    url = f"{ROR_URL}?{urlencode({'query': query})}"
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=5) as response:
            data = json.load(response)
    except (OSError, ValueError):
        return []

    results = []
    for item in data.get("items", [])[:limit]:
        name = _display_name(item)
        if name:
            results.append({"name": name, "country": _country(item)})

    cache.set(key, results, 60 * 60 * 24)
    return results