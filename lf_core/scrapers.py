"""LeadsFind (LF) - scrapers.
Sources: Google Maps (SerpAPI) | JustDial | OpenStreetMap | Web Search | All-in-one | Demo
Logic adapted from D:\\Scrapegraph-ai (serpapi + overpass scripts), generalised.
"""
import os
import re
import time
import random
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0 Safari/537.36",
           "Accept-Language": "en-IN,en;q=0.9"}

SOURCES = {
    "serpapi": "Google Maps",
    "justdial": "JustDial",
    "web": "Web Search",
}

PHONE_RE = re.compile(r"\+?91[\s\-]?[6-9]\d{4}[\s\-]?\d{5}|\b[6-9]\d{9}\b")


def _digits(phone: str) -> str:
    return re.sub(r"\D", "", phone or "")[-10:]


# ---------- Google Maps via SerpAPI ----------
def serpapi_fetch(location: str, business: str, place_name: str = "", limit: int = 20,
                  api_key: str = "") -> list:
    from serpapi import GoogleSearch  # pip: google-search-results
    # area khaali ho to sirf city-wide query (extra space nahi)
    parts = [business, "in", location] + ([place_name] if place_name.strip() else [])
    q = " ".join(parts)
    params_base = {"engine": "google_maps", "q": q, "type": "search", "api_key": api_key}
    out, seen = [], set()
    # 20 results/page; max 8 pages (~160) — usse zyada Google repeat karne lagta hai
    pages = min(max(1, (limit + 19) // 20), 8)
    for start in range(0, pages * 20, 20):
        params = dict(params_base)
        params["start"] = start
        res = GoogleSearch(params).get_dict()
        if "error" in res:
            raise RuntimeError(f"SerpAPI error: {res['error']}")
        local = res.get("local_results", []) or []
        if not local:
            break
        for r in local:
            pid = r.get("place_id") or r.get("data_id") or r.get("title")
            if pid in seen:
                continue
            seen.add(pid)
            website = r.get("website") or (r.get("links", {}) or {}).get("website") or ""
            out.append({
                "business_name": r.get("title", ""),
                "phone": r.get("phone") or "",
                "address": r.get("address", ""),
                "rating": r.get("rating", ""),
                "reviews": r.get("reviews") or "",
                "hours": r.get("hours") or str(r.get("operating_hours", "") or ""),
                "website": website if website else "NO WEBSITE",
                "maps_link": r.get("link") or "",
                "source": "Google Maps",
            })
            if len(out) >= limit:
                break
        if len(out) >= limit:
            break
        time.sleep(1.2)
    return out[:limit]


# ---------- Bulk: ek click me 300/800/1800 leads ----------
BULK_CALL_BUDGET = 12  # ek run me max SerpAPI calls (free quota bachao)


def _gmaps_round(q: str, pages: int, api_key: str, out: list, seen: set,
                 budget: list):
    """Ek query ke kayi pages lao, budget ghatate jao."""
    from serpapi import GoogleSearch
    for start in range(0, pages * 20, 20):
        if budget[0] <= 0:
            break
        res = GoogleSearch({"engine": "google_maps", "q": q, "type": "search",
                            "start": start, "api_key": api_key}).get_dict()
        budget[0] -= 1
        if "error" in res:
            raise RuntimeError(f"SerpAPI error: {res['error']}")
        local = res.get("local_results", []) or []
        if not local:
            break
        fresh = 0
        for r in local:
            pid = r.get("place_id") or r.get("data_id") or r.get("title")
            if pid in seen:
                continue
            seen.add(pid)
            fresh += 1
            website = r.get("website") or (r.get("links", {}) or {}).get("website") or ""
            out.append({
                "business_name": r.get("title", ""),
                "phone": r.get("phone") or "",
                "address": r.get("address", ""),
                "rating": r.get("rating", ""),
                "reviews": r.get("reviews") or "",
                "hours": r.get("hours") or str(r.get("operating_hours", "") or ""),
                "website": website if website else "NO WEBSITE",
                "maps_link": r.get("link") or "",
                "source": "Google Maps",
            })
        if fresh == 0:
            break  # repeat results = aage kuch naya nahi
        time.sleep(1.0)


def fetch_bulk(location: str, business: str, place_name: str = "", limit: int = 100,
               api_key: str = "") -> list:
    """Bade packs (300/800/1800) ek click me: kayi query-variant + dedup.
    Jitna mila utna wapas; credits sirf delivered pe katega."""
    if not api_key:
        raise RuntimeError("SerpAPI key nahi hai.")
    loc = location.strip()
    plc = place_name.strip()
    queries = [f"{business} in {loc}" + (f" {plc}" if plc else "")]
    if plc:
        queries.append(f"{business} in {plc}")
    queries += [f"best {business} in {loc}",
                f"{business} near {loc}",
                f"{business} {loc} phone contact"]
    out, seen, budget = [], set(), [BULK_CALL_BUDGET]
    for q in queries:
        _gmaps_round(q, 3, api_key, out, seen, budget)
        if len(out) >= limit or budget[0] <= 0:
            break
    return out[:limit]


# ---------- JustDial via Google (JD direct anti-bot se blocked hai) ----------
def justdial_fetch(location: str, business: str, place_name: str = "", limit: int = 20,
                   api_key: str = "") -> list:
    """JustDial apne pages pe bot-block lagata hai, isliye Google me
    `site:justdial.com` search karke JD-listed shops nikalte hain.
    Isme Google key chahiye (SerpAPI wali hi chalegi)."""
    if not api_key:
        raise RuntimeError("JustDial source abhi busy hai — Google Maps try karo.")
    from serpapi import GoogleSearch
    q = f"site:justdial.com {business} {place_name} {location}".strip()
    out, seen = [], set()
    for start in (0, 10, 20, 30, 40):
        res = GoogleSearch({"engine": "google", "q": q, "num": 10,
                            "start": start, "api_key": api_key}).get_dict()
        if "error" in res:
            raise RuntimeError(f"SerpAPI error: {res['error']}")
        organic = res.get("organic_results", []) or []
        if not organic:
            break
        for r in organic:
            link = r.get("link", "")
            if "justdial.com" not in link or link in seen:
                continue
            seen.add(link)
            title = re.sub(r"\s*[-|–]\s*Just ?Dial.*$", "", r.get("title", ""),
                           flags=re.I).strip()
            snippet = r.get("snippet", "") or ""
            m = PHONE_RE.search(title + " " + snippet)
            out.append({
                "business_name": title[:120] or "JustDial listing",
                "phone": m.group(0) if m else "",
                "address": snippet[:200] or location,
                "rating": "",
                "reviews": "",
                "hours": "",
                "website": "NO WEBSITE",
                "maps_link": link,
                "source": "JustDial",
            })
            if len(out) >= limit:
                break
        if len(out) >= limit:
            break
        time.sleep(1.2)
    if not out:
        raise RuntimeError("JustDial listings nahi mili. Spelling ya city badal ke dekho.")
    return out[:limit]


# ---------- OpenStreetMap (free, no key) ----------
def _bbox_for_location(location: str):
    r = requests.get("https://nominatim.openstreetmap.org/search",
                     params={"q": location, "format": "json", "limit": 1},
                     headers={"User-Agent": "LeadsFind/1.0"}, timeout=20)
    r.raise_for_status()
    j = r.json()
    if not j:
        return (28.60, 77.30, 28.80, 77.55)  # fallback Ghaziabad
    b = j[0]["boundingbox"]
    return (float(b[0]), float(b[2]), float(b[1]), float(b[3]))


def overpass_fetch(location: str, business: str, place_name: str = "", limit: int = 20) -> list:
    s, w, n, e = _bbox_for_location(f"{place_name} {location}".strip() or location)
    # halki query: naam-match + category-tag match (poora dump timeout karta hai)
    query = f"""
[out:json][timeout:30];
(
  node["name"~"{business}",i]({s},{w},{n},{e});
  way["name"~"{business}",i]({s},{w},{n},{e});
  node["shop"~"{business}",i]({s},{w},{n},{e});
  node["amenity"~"{business}",i]({s},{w},{n},{e});
  node["healthcare"~"{business}",i]({s},{w},{n},{e});
  node["office"~"{business}",i]({s},{w},{n},{e});
  node["craft"~"{business}",i]({s},{w},{n},{e});
);
out body;
"""
    r = requests.post("https://overpass-api.de/api/interpreter",
                      data={"data": query}, timeout=60,
                      headers={"User-Agent": "LeadsFind/1.0 (contact: care@leadsfind.in)"})
    r.raise_for_status()
    els = r.json().get("elements", [])
    out = []
    for el in els[:limit * 3]:
        tags = el.get("tags", {})
        name = tags.get("name", "")
        if business.lower() not in name.lower():
            if len(out) > limit // 3 and not name:
                continue
        out.append({
            "business_name": name or f"{business} outlet",
            "phone": tags.get("phone") or tags.get("contact:phone") or "",
            "address": " ".join([tags.get("addr:street", ""), tags.get("addr:city", location),
                                 tags.get("addr:postcode", "")]).strip(),
            "rating": "",
            "reviews": "",
            "hours": tags.get("opening_hours", ""),
            "website": tags.get("website") or tags.get("contact:website") or "NO WEBSITE",
            "maps_link": "",
            "source": "OpenStreetMap",
        })
        if len(out) >= limit:
            break
    return out[:limit]


# ---------- Web Search via DuckDuckGo (free: websites + phone regex) ----------
def _web_parse(results, out: list, seen: set, location: str, limit: int):
    for r in results:
        href = r.get("href", "")
        if not href or href in seen or "justdial" in href or "indiamart" in href:
            continue
        seen.add(href)
        body = r.get("body", "") or ""
        m = PHONE_RE.search(r.get("title", "") + " " + body)
        domain = re.sub(r"^https?://(www\.)?", "", href).split("/")[0]
        out.append({
            "business_name": (r.get("title", "") or domain)[:120],
            "phone": m.group(0) if m else "",
            "address": body[:200],
            "rating": "",
            "reviews": "",
            "hours": "",
            "website": href,
            "maps_link": "",
            "source": "Web Search",
        })
        if len(out) >= limit:
            break
    return out


def web_fetch(location: str, business: str, place_name: str = "", limit: int = 20) -> list:
    from ddgs import DDGS
    q = f"{business} {place_name} {location} contact phone website".strip()
    out, seen = [], set()
    try:
        results = DDGS().text(q, max_results=min(limit * 2, 80))
    except Exception as e:
        raise RuntimeError(f"Web search fail: {e}")
    _web_parse(results, out, seen, location, limit)
    if not out:
        raise RuntimeError("Web search se kuch nahi mila. Spelling badal ke dekho.")
    return out[:limit]


def web_bulk(location: str, business: str, place_name: str = "", limit: int = 100) -> list:
    """FREE + UNLIMITED bulk: kayi query-variant, zero cost, koi budget cap nahi.
    Bade packs (300/800/1800) bina SerpAPI kharch ke fulfill karo."""
    from ddgs import DDGS
    loc, plc = location.strip(), place_name.strip()
    queries = [
        f"{business} {plc} {loc} contact phone website".strip(),
        f"best {business} in {loc}",
        f"{business} in {loc} website",
        f"{business} {loc} phone number contact",
        f"top {business} {loc}",
        f"{business} {loc} address",
    ]
    out, seen = [], set()
    try:
        ddgs = DDGS()
        for q in queries:
            try:
                results = ddgs.text(q, max_results=100)
            except Exception:
                continue
            _web_parse(results, out, seen, location, limit)
            if len(out) >= limit:
                break
            time.sleep(1.0)
    except Exception as e:
        if not out:
            raise RuntimeError(f"Web search fail: {e}")
    if not out:
        raise RuntimeError("Web search se kuch nahi mila. Spelling badal ke dekho.")
    return out[:limit]


# ---------- Demo ----------
def demo_fetch(location: str, business: str, place_name: str = "", limit: int = 20) -> list:
    random.seed(hash((location, business, place_name)) % (2 ** 32))
    base = place_name or location
    out = []
    for i in range(1, limit + 1):
        has_site = random.random() > 0.5
        has_phone = random.random() > 0.25
        out.append({
            "business_name": f"{business.title()} #{i} - {base}",
            "phone": f"+91 98{random.randint(10000000, 99999999)}" if has_phone else "",
            "address": f"Shop {i}, Main Market, {base}",
            "rating": round(random.uniform(3.5, 5.0), 1),
            "reviews": random.randint(5, 500),
            "hours": "10:00 AM - 8:00 PM",
            "website": f"https://example-{i}.com" if has_site else "NO WEBSITE",
            "maps_link": "",
            "source": "Demo",
        })
    return out


# ---------- All-in-one: sab merge + dedup ----------
def fetch_all(location: str, business: str, place_name: str = "", limit: int = 20,
              serpapi_key: str = "") -> list:
    merged, errors = [], []
    jobs = []
    if serpapi_key:
        jobs.append(("Google", lambda: serpapi_fetch(location, business, place_name, limit, serpapi_key)))
        jobs.append(("JustDial", lambda: justdial_fetch(location, business, place_name, limit, serpapi_key)))
    jobs += [
        ("OSM", lambda: overpass_fetch(location, business, place_name, limit)),
        ("Web", lambda: web_fetch(location, business, place_name, limit)),
    ]
    for name, fn in jobs:
        try:
            merged.extend(fn())
        except Exception as e:
            errors.append(f"{name}: {str(e)[:80]}")
        if len(merged) >= limit * 2:
            break
    # dedup: naam + phone digits
    seen, out = set(), []
    for L in merged:
        key = (L.get("business_name", "").lower().strip(), _digits(L.get("phone", "")))
        if key[0] and key not in seen:
            seen.add(key)
            out.append(L)
        if len(out) >= limit:
            break
    if not out:
        raise RuntimeError("Koi source se leads nahi mili. " + " | ".join(errors)[:200])
    return out


# ---------- Tick filters: client apni marzi se ----------
def apply_filters(leads: list, need_phone: bool = False,
                  want_with: bool = True, want_without: bool = True) -> list:
    """✅ Number wale | 🌐 Website wale | 🚫 Bina website.
    Dono website tick = sab. Dono untick = sab (filter off)."""
    out = []
    for L in leads:
        has_phone = bool((L.get("phone") or "").strip())
        has_site = (L.get("website") or "") not in ("", "NO WEBSITE")
        if need_phone and not has_phone:
            continue
        if want_with and not want_without and not has_site:
            continue
        if want_without and not want_with and has_site:
            continue
        out.append(L)
    return out


def fetch_leads(platform: str, location: str, business: str, place_name: str,
                limit: int, serpapi_key: str = "") -> list:
    platform = (platform or "demo").lower()
    if platform == "serpapi":
        if not serpapi_key:
            raise RuntimeError("Google Maps abhi busy hai — Web Search try karo.")
        return serpapi_fetch(location, business, place_name, limit, serpapi_key)
    if platform == "justdial":
        return justdial_fetch(location, business, place_name, limit, serpapi_key)
    if platform == "overpass":
        return overpass_fetch(location, business, place_name, limit)
    if platform == "web":
        return web_fetch(location, business, place_name, limit)
    if platform == "all":
        return fetch_all(location, business, place_name, limit, serpapi_key)
    return demo_fetch(location, business, place_name, limit)
