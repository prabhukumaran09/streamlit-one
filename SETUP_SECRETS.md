# 🔑 How to Configure Credentials (One-Time Setup)

## Option A — Streamlit Cloud Dashboard (Recommended)
> Update the access token here daily in 30 seconds. No code changes needed.

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Find your deployed app → click **⋮ (three dots)** → **Settings**
3. Click **Secrets** tab
4. Paste this and fill in your values:

```toml
KITE_API_KEY      = "xxxxxxxxxxxxxxxx"
KITE_API_SECRET   = "xxxxxxxxxxxxxxxx"
KITE_ACCESS_TOKEN = "xxxxxxxxxxxxxxxx"
```

5. Click **Save** — app reloads automatically ✅

**Daily routine:** Every morning before 9:15 AM IST, just update `KITE_ACCESS_TOKEN` value here.

---

## Option B — Local Development (`secrets.toml`)
> For running the app on your own machine.

Edit `.streamlit/secrets.toml`:
```toml
KITE_API_KEY      = "xxxxxxxxxxxxxxxx"
KITE_API_SECRET   = "xxxxxxxxxxxxxxxx"
KITE_ACCESS_TOKEN = "xxxxxxxxxxxxxxxx"
```

⚠️ This file is in `.gitignore` — it will **never** be pushed to GitHub.

---

## Option C — Environment Variables
> Useful for Docker, Raspberry Pi, or CI/CD pipelines.

```bash
export KITE_API_KEY="xxxxxxxxxxxxxxxx"
export KITE_API_SECRET="xxxxxxxxxxxxxxxx"
export KITE_ACCESS_TOKEN="xxxxxxxxxxxxxxxx"
streamlit run app.py
```

---

## Priority Order
The app checks credentials in this order:
1. **Streamlit Secrets** (`st.secrets`) ← highest priority
2. **Environment variables** (`os.environ`)
3. **Manual UI input** (the fields on the main page) ← fallback

---

## Daily Token Refresh Workflow (Streamlit Cloud)

Your existing `token_refresh_mobile.py` script generates the new access token.
After running it:

1. Copy the new `access_token` value
2. Open Streamlit Cloud → your app → Settings → Secrets
3. Update `KITE_ACCESS_TOKEN = "new_token_here"`
4. Save → done in under 30 seconds ✅

