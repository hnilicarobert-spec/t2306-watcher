import os, re, json, time, hashlib
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

SERPER_KEY = os.environ["SERPER_API_KEY"]
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
PUSHOVER_TOKEN = os.environ.get("PUSHOVER_TOKEN")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")

STATE = Path("state.json")
RESULTS = Path("results.json")
REFERENCE_IMAGE = os.environ.get(
    "REFERENCE_IMAGE_URL",
    "https://scd.sk/wp-content/uploads/2025/09/Hrescak-Stolicka-T2306-768x1152.jpg"
)

# Deliberately broad: sellers often omit "T2306".
QUERIES = [
    'T2306 Hreščák',
    '"T 2306" Hreščák',
    'Kodreta Myjava chair',
    'Kodreta Myjava židle',
    'Kodreta Myjava stolička',
    'Hreščák židle',
    'Hrescak chair',
    'retro židle Kodreta',
    'retro stolička Kodreta',
    'chromová trubková židle čalouněná',
    'ohýbaná kovová židle Kodreta',
]

DOMAINS = [
    "bazos.cz", "bazos.sk", "aukro.cz", "aukro.sk",
    "sbazar.cz", "facebook.com/marketplace",
    "modrykonik.cz", "odklepnuto.cz",
    "ebay.de", "ebay.com"
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; T2306-Watcher/1.0)"}

def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {
        "seen": {},
        "last_scan": None,
        "last_scan_started": None,
        "websites_checked": [],
        "website_status": {}
    }

def save_state(s):
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2))

def serper(q):
    r = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"},
        json={"q": q, "gl": "cz", "hl": "cs", "num": 20},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("organic", [])

def get_og_image(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if r.status_code >= 400:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        for prop in ["og:image", "twitter:image"]:
            tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
            if tag and tag.get("content"):
                return tag["content"]
    except Exception:
        return None
    return None


def page_looks_inactive(text, title=""):
    blob = (title + "\n" + text).lower()
    phrases = [
        "inzerát byl odstraněn", "inzerát bol odstránený",
        "inzerát již není aktivní", "inzerat uz nie je aktivny",
        "nabídka byla ukončena", "ponuka bola ukončená",
        "listing has ended", "listing is no longer available",
        "this listing is no longer available", "item sold",
        "this item has been sold", "položka byla prodána",
        "inzerát nenalezen", "inzerát neexistuje",
        "stránka neexistuje", "page not found",
        "404 not found", "410 gone",
    ]
    return any(x in blob for x in phrases)

def verify_active(url):
    """
    Re-check a listing immediately before alerting.
    Returns (active, final_url, page_title, reason).
    A transient 403/429 is treated as 'unknown', not automatically inactive,
    because marketplaces frequently protect pages from automated clients.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        final_url = r.url
        if r.status_code in (404, 410):
            return False, final_url, "", f"HTTP {r.status_code}"
        if r.status_code in (403, 429, 503):
            return None, final_url, "", f"HTTP {r.status_code} (unknown)"
        if r.status_code >= 400:
            return False, final_url, "", f"HTTP {r.status_code}"

        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        body = soup.get_text(" ", strip=True)
        if page_looks_inactive(body[:200000], title):
            return False, final_url, title, "inactive wording on page"

        # A redirected marketplace URL can be a deleted listing or a generic
        # category page. Treat a major domain/path change as unknown, not dead.
        return True, final_url, title, "page loaded"
    except requests.RequestException as e:
        return None, url, "", f"request error: {e}"

def verify_by_search(url):
    """Secondary check: search the exact URL. Returns True/False/None."""
    try:
        rows = serper(f'"{url}"')
        if not rows:
            return None
        for row in rows:
            if row.get("link") == url or url.rstrip("/") in row.get("link", ""):
                txt = (row.get("title","") + " " + row.get("snippet","")).lower()
                if page_looks_inactive(txt):
                    return False
                return True
        return None
    except Exception:
        return None

def ai_visual_check(image_url, title, snippet):
    prompt = f"""
You are identifying a specific vintage chair model.

Target: Jaroslav Hreščák / Kodreta Myjava T2306.
The target has a minimalist chrome-plated bent tubular-steel frame, four straight legs,
a fabric/leatherette seat and a separate rectangular-ish upholstered backrest attached to
the rear uprights. It is the armless T2306; do NOT confuse it with T2307 (with arms) or
T2403 (an armchair).

Candidate listing title: {title}
Candidate snippet: {snippet}

Compare the candidate image with the target design. Return ONLY JSON:
{{"match": 0-100, "is_t2306": true/false, "reason": "short reason"}}

Give a high score only when the geometry visibly matches. Different upholstery color,
minor restoration, or a different camera angle should not disqualify it.
"""
    body = {
        "model": MODEL,
        "input": [{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": REFERENCE_IMAGE, "detail": "high"},
                {"type": "input_image", "image_url": image_url, "detail": "high"},
            ],
        }],
    }
    r = requests.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
        json=body,
        timeout=90,
    )
    r.raise_for_status()
    data = r.json()
    text = data.get("output_text", "").strip()
    m = re.search(r'\{.*\}', text, re.S)
    if not m:
        return {"match": 0, "is_t2306": False, "reason": "AI response could not be parsed"}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {"match": 0, "is_t2306": False, "reason": "AI JSON parse failed"}

def notify(items):
    if not (PUSHOVER_TOKEN and PUSHOVER_USER and items):
        return
    lines = ["T2306 WATCHER — new possible listing(s):"]
    for x in items[:8]:
        lines.append(f"\n{x['match']}% — {x['title']}\n{x['url']}")
    r = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "title": "T2306 found",
            "message": "\n".join(lines)[:4000],
            "priority": 1,
        },
        timeout=20,
    )
    r.raise_for_status()

def main():
    state = load_state()
    candidates = {}
    for q in QUERIES:
        try:
            rows = serper(q)
        except Exception as e:
            print("Search failed:", q, e)
            continue
        for row in rows:
            url = row.get("link")
            if not url or "google." in url:
                continue
            host = urlparse(url).netloc.lower()
            if not any(d in host or d in url.lower() for d in DOMAINS):
                continue
            candidates[url] = {
                "url": url,
                "title": row.get("title", ""),
                "snippet": row.get("snippet", ""),
                "query": q,
            }

    new_matches = []
    for url, c in candidates.items():
        key = hashlib.sha256(url.encode()).hexdigest()[:24]

        # Always re-check previously discovered listings. This prevents
        # notifications for chairs that have already been sold/deleted.
        active, final_url, live_title, active_reason = verify_active(url)
        c["active"] = active
        c["active_reason"] = active_reason
        if active is False:
            if key in state["seen"]:
                state["seen"][key]["active"] = False
                state["seen"][key]["inactive_reason"] = active_reason
            continue
        if active is None:
            # If the site blocks automated verification, use an exact-URL
            # search as a secondary signal.
            search_active = verify_by_search(url)
            c["active"] = search_active
            c["active_reason"] = f"page check unknown; exact-URL search={search_active}"
            if search_active is False:
                if key in state["seen"]:
                    state["seen"][key]["active"] = False
                continue

        # Existing active listings are retained in results, but only NEW
        # candidates can generate a push notification.
        is_new = key not in state["seen"]
        img = get_og_image(url)
        c["image"] = img
        c["match"] = 0
        c["is_t2306"] = False
        c["reason"] = "No listing image available"

        if img:
            try:
                verdict = ai_visual_check(img, c["title"], c["snippet"])
                c.update(verdict)
            except Exception as e:
                c["reason"] = f"visual check failed: {e}"

        # Text + visual gate. A title-only hit can still be saved for manual review.
        text_blob = (c["title"] + " " + c["snippet"]).lower()
        text_hit = any(k in text_blob for k in [
            "t2306", "t 2306", "hrescak", "hreščák", "kodreta", "myjava"
        ])
        if c["match"] >= 72 or (text_hit and c["match"] >= 45):
            c["new"] = is_new
            c["verified_active"] = c.get("active") is True
            if is_new:
                new_matches.append(c)

        state["seen"][key] = {
            "url": url, "title": c["title"], "match": c["match"],
            "first_seen": state["seen"].get(key, {}).get(
                "first_seen",
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            ),
            "active": c.get("active"),
            "last_checked": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "match": c.get("match", 0)
        }

    state["last_scan"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    save_state(state)

    # Keep a useful dashboard file, newest first.
    old = json.loads(RESULTS.read_text()) if RESULTS.exists() else []
    merged = new_matches + old
    unique = {}
    for x in merged:
        unique[x["url"]] = x
    merged = list(unique.values())
    merged.sort(key=lambda x: x.get("match", 0), reverse=True)
    RESULTS.write_text(json.dumps(merged[:100], ensure_ascii=False, indent=2))

    notify(sorted(new_matches, key=lambda x: x.get("match", 0), reverse=True))
    print(f"Scanned {len(candidates)} pages; {len(new_matches)} new possible matches.")

if __name__ == "__main__":
    main()
