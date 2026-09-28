# iPhone one-tap setup

The simplest setup is a Home Screen bookmark/Shortcut that opens your GitHub Pages dashboard.

## Option A — zero code on the iPhone
1. Enable GitHub Pages for this repository: **Settings → Pages → Deploy from branch → main → /(root)**.
2. Open the resulting `https://YOURNAME.github.io/YOUR-REPO/` page in Safari.
3. Share → **Add to Home Screen**.
4. Name it **T2306 Watcher**.

One tap then shows the latest results.

## Option B — a real iOS Shortcut
Create a Shortcut with:
1. **URL** = your GitHub Pages URL.
2. **Open URLs**.
3. Add it to the Home Screen.

The scheduled GitHub Action does the actual scanning every 15 minutes, so the iPhone itself does not need to stay open.

## Facebook Marketplace
Facebook frequently requires login and may not expose individual listings to automated search. Keep the Facebook Marketplace search link in the Shortcut as a second action. The watcher still searches the public web for indexed Facebook listings, but it should not be treated as a complete Facebook crawler.

## Important
Do not put your Serper/OpenAI/Pushover API keys into the Shortcut. Keep them as GitHub repository secrets.


# Complete first-time setup

## A. Create the GitHub account
1. On your iPhone, open GitHub and create/sign in to an account.
2. Create a new repository, e.g. `t2306-watcher`.
3. You can make it public or private. If using GitHub Free, remember that a GitHub Pages site is publicly accessible, so don't publish API keys or sensitive information.

## B. Upload the project
1. Download the ZIP from ChatGPT.
2. Unzip it.
3. In your GitHub repository choose **Add file → Upload files**.
4. Upload every file and folder from the unzipped project, preserving `.github/workflows/watch.yml`.
5. Commit to the `main` branch.

## C. Create the search API key
1. Create a Serper account.
2. Create an API key.
3. In GitHub open your repository → **Settings → Secrets and variables → Actions**.
4. Choose **New repository secret**.
5. Name: `SERPER_API_KEY`
6. Paste the Serper key.
7. Save.

## D. Create the OpenAI API key
1. Open the OpenAI API platform and create an API key.
2. GitHub → repository → **Settings → Secrets and variables → Actions**.
3. **New repository secret**.
4. Name: `OPENAI_API_KEY`
5. Paste the key.
6. Save.

Do NOT put this key into `watcher.py`, `index.html`, the iPhone Shortcut, or a public webpage.

## E. Optional push notifications
For push notifications install Pushover on the iPhone and create its application/user credentials.
Add two GitHub Actions secrets:
- `PUSHOVER_TOKEN`
- `PUSHOVER_USER`

If you skip this step, the watcher still works and the webpage still updates.

## F. Start the watcher manually
1. GitHub → repository → **Actions**.
2. Select **T2306 chair watcher**.
3. Press **Run workflow**.
4. Wait for the run to finish.
5. Open the run and check the log.
6. You should see something like `Scanned X pages; Y new possible matches.`

## G. Turn on the iPhone dashboard
1. GitHub → repository → **Settings → Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select `main` and `/ (root)`.
4. Save.
5. GitHub will show the published URL.
6. Open it in Safari.
7. Share → **Add to Home Screen**.
8. Name it `T2306 Watcher`.

GitHub documents this Pages setup here:
https://docs.github.com/en/pages/quickstart

## H. Test the one-tap system
Tap the new **T2306 Watcher** icon.
You should see the dashboard and any currently detected candidates.

## I. What happens automatically
The GitHub Action runs on its schedule. It searches, checks images, verifies that listings are still active, stores the results, and sends a push alert for a new qualifying listing.

If a listing later disappears, the next scan marks it inactive and it will no longer be treated as a live candidate.

## J. Facebook
For Facebook Marketplace, also create a Safari/iPhone Shortcut that opens your preferred Marketplace search. Facebook can require login and may not expose individual listings to public automated requests. The watcher therefore treats Facebook as supplemental rather than promising complete Marketplace coverage.
