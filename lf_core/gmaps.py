"""Google Maps (Free) — gosom/google-maps-scraper sidecar (localhost:8080).
entrypoint.sh isko background me chalata hai (Render/Docker dono me).
Safety: -c 1 + ek job at a time + chhota depth = RAM aur IP-block dono safe.
Agar Google Maps fail ho toh caller (scrapers.fetch_leads) Web Search pe fallback karta hai.
"""
import csv
import io
import os
import threading
import time

import requests

GMAPS_BASE = os.getenv("GMAPS_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
_JOB_LOCK = threading.Lock()

NOMINATIM_HEADERS = {"User-Agent": "LeadsFind/1.0"}


def gmaps_available(timeout: float = 2.0) -> bool:
    try:
        return requests.get(f"{GMAPS_BASE}/api/v1/jobs", timeout=timeout).ok
    except Exception:
        return False


def _geocode(place: str):
    r = requests.get("https://nominatim.openstreetmap.org/search",
                     params={"q": place, "format": "json", "limit": 1},
                     headers=NOMINATIM_HEADERS, timeout=20)
    r.raise_for_status()
    j = r.json()
    if not j:
        return None
    return str(j[0]["lat"]), str(j[0]["lon"])


def gmaps_fetch(location: str, business: str, place_name: str = "",
                limit: int = 20) -> list:
    if not gmaps_available():
        raise RuntimeError("Google Maps (Free) abhi shuru nahi hai — Web Search try karo.")
    if not _JOB_LOCK.acquire(blocking=False):
        raise RuntimeError("Ek aur Google Maps search abhi chal rahi hai — "
                           "1 minute ruko, phir try karo (free instance pe ek job at a time).")
    job_id = None
    try:
        q_place = f"{place_name} {location}".strip() or location.strip()
        coords = _geocode(q_place) or _geocode(location.strip())
        if not coords:
            raise RuntimeError("City ka location nahi mila — naam theek likh ke dekho.")
        lat, lon = coords

        kw = business.strip()
        if place_name.strip():
            keyword = f"{kw} in {place_name.strip()}, {location.strip()}"
        else:
            keyword = f"{kw} in {location.strip()}"

        # RAM + block safe: chhota depth, email off (website crawl nahi), ek hi job
        depth = min(8, max(3, int(limit / 8) + 2))
        max_time = 150
        body = {
            "name": "leadsfind", "keywords": [keyword], "lang": "en", "zoom": 15,
            "lat": lat, "lon": lon, "fast_mode": False, "radius": 10000,
            "depth": depth, "email": False, "max_time": max_time,
        }
        r = requests.post(f"{GMAPS_BASE}/api/v1/jobs", json=body, timeout=30)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Google Maps job nahi bana (HTTP {r.status_code}) — "
                               "Web Search try karo.")
        job_id = (r.json() or {}).get("id")
        if not job_id:
            raise RuntimeError("Google Maps job id nahi mila — Web Search try karo.")

        deadline = time.time() + max_time + 30
        status = None
        while time.time() < deadline:
            s = requests.get(f"{GMAPS_BASE}/api/v1/jobs/{job_id}", timeout=15)
            data = s.json() or {}
            status = data.get("Status") or data.get("status")
            if status in ("ok", "failed"):
                break
            time.sleep(5)
        if status != "ok":
            raise RuntimeError("Google Maps abhi busy hai (rate-limit/IP throttle) — "
                               "thodi der baad retry karo ya Web Search use karo.")

        d = requests.get(f"{GMAPS_BASE}/api/v1/jobs/{job_id}/download", timeout=30)
        rows = list(csv.DictReader(io.StringIO(d.text)))
        out = []
        for row in rows:
            website = (row.get("website") or "").strip()
            out.append({
                "business_name": (row.get("title") or "").strip(),
                "phone": (row.get("phone") or "").strip(),
                "address": (row.get("address") or "").strip(),
                "rating": str(row.get("review_rating") or "").strip(),
                "reviews": str(row.get("review_count") or "").strip(),
                "hours": (row.get("open_hours") or "").strip(),
                "website": website if website else "NO WEBSITE",
                "maps_link": (row.get("link") or "").strip(),
                "source": "Google Maps (Free)",
                "emails": (row.get("emails") or "").strip(),
                "category": (row.get("category") or "").strip(),
            })
            if len(out) >= limit:
                break
        if not out:
            raise RuntimeError("Google Maps se is baar kuch nahi mila — "
                               "thodi der baad retry karo ya Web Search use karo.")
        return out
    finally:
        if job_id:
            try:
                requests.delete(f"{GMAPS_BASE}/api/v1/jobs/{job_id}", timeout=10)
            except Exception:
                pass
        _JOB_LOCK.release()
