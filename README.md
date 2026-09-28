# T2306 Watcher — iPhone-first vintage chair finder

This project watches public web results for the **Jaroslav Hreščák / Kodreta Myjava T2306** chair.

It intentionally uses two signals:

1. **Text search** — catches listings that say T2306, T 2306, Hreščák/Hrescak, Kodreta/Myjava, retro chair, etc.
2. **Visual check** — downloads the listing's `og:image` when available and asks a vision-capable model whether the pictured chair resembles T2306.

This matters because sellers often don't know the model number.

The official Slovak Design Centre reference image is used by default:
`https://scd.sk/wp-content/uploads/2025/09/Hrescak-Stolicka-T2306-768x1152.jpg`

## Marketplaces / sources

Configured for searches that can surface:
- Bazoš Czech Republic / Slovakia
- Aukro Czech Republic / Slovakia
- Sbazar
- Facebook Marketplace public/indexed pages
- eBay
- other indexed classifieds

Add more domains in `watcher.py`.

## Setup

### 1. Create a GitHub repository
Create a new private or public repository and upload all files in this folder.

### 2. Add repository secrets

Repository → Settings → Secrets and variables → Actions → New repository secret:

- `SERPER_API_KEY` — Serper Google Search API key
- `OPENAI_API_KEY` — OpenAI API key
- `PUSHOVER_TOKEN` — optional
- `PUSHOVER_USER` — optional

Serper is used because it provides structured Google search results. The OpenAI API is used only for the visual comparison.

### 3. Enable GitHub Actions
The workflow runs every 15 minutes and can also be started manually with **Run workflow**.

### 4. Enable GitHub Pages
Settings → Pages → Deploy from branch → `main` → `/ (root)`.

Open the resulting Pages URL on the iPhone and use **Share → Add to Home Screen**.

### 5. Notifications
Pushover is optional. Without it, the dashboard still updates.

## Tuning the visual detector

The default threshold is:
- 72+ = strong visual candidate
- 45+ = candidate when text strongly indicates T2306/Kodreta/Hreščák

If you get too many false positives, raise 72 to 80.
If you miss too many restored/reupholstered chairs, lower 72 to 65.

## Strongly recommended improvement

Put 3–5 additional reference photographs of genuine T2306 chairs into your own image host and modify the script to send multiple references. Different upholstery, lighting, perspective and restoration can otherwise confuse a single-reference comparison.

Also keep T2307 out of the target: T2307 is the related version with armrests.

## Cost

The search API and vision API are external services and may charge according to their current pricing. GitHub Actions itself can be used within the limits of the GitHub account/plan.

## Why not scrape Facebook directly?

Marketplace is commonly login-gated and its public pages are not a reliable API. The watcher therefore searches what is publicly indexed and leaves Facebook itself as a manual/Shortcut search surface.

## Suggested search vocabulary

The script deliberately searches:
- T2306
- T 2306
- Jaroslav Hreščák
- Jaroslav Hrescak
- Kodreta Myjava
- retro židle
- retro stolička
- chrome/tubular steel chair
- bent tubular metal chair
- upholstered Czechoslovak chair

That is important because a seller may write only “retro židle” or “staré kancelářské židle”.


## Active-listing double check

Every scan now re-checks previously discovered URLs before they can produce an alert.

The watcher:
1. Loads the listing URL.
2. Checks the HTTP response.
3. Looks for common sold/deleted/not-found wording in the page.
4. If the marketplace blocks the automated request with 403/429/503, performs a second exact-URL web search where possible.
5. Suppresses the candidate if the evidence says the listing is gone.
6. Stores `active`, `last_checked`, and the last visual score in `state.json`.

A blocked page is treated as **unknown**, not automatically dead. This avoids losing good chairs simply because a marketplace temporarily blocks an automated request.

No automated checker can guarantee 100% correctness for login-gated or JavaScript-only marketplaces, so Facebook Marketplace remains a special case.
