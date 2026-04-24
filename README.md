# 📈 Intraday Option Scanner — Camarilla R4 Breakout

Scans all NSE F&O stocks for ATM option breakouts above Camarilla R4 level, using 15-minute intraday candles via Kite Connect (Zerodha).

---

## 🔧 Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Add Kite credentials
Edit `.streamlit/secrets.toml`:
```toml
KITE_API_KEY      = "your_api_key"
KITE_API_SECRET   = "your_api_secret"
KITE_ACCESS_TOKEN = "your_access_token"   # refresh daily before 9:15 AM IST
```
**OR** enter them live in the app sidebar (no restart needed).

### 3. Run locally
```bash
streamlit run app.py
```

### 4. Deploy to Streamlit Community Cloud
- Push this folder to a GitHub repo
- Go to share.streamlit.io → New app → select your repo
- Add secrets in the Streamlit Cloud dashboard (Settings → Secrets)

---

## 📊 How It Works

| Step | Logic |
|------|-------|
| Universe | ~180 NSE F&O stocks |
| ATM Strike | Nearest strike to current spot price |
| Candle | Last **completed** 15-min candle of the ATM option |
| R4 Formula | `Close + (High − Low) × 1.1 / 2` |
| Signal | **LTP > R4** → breakout triggered |
| Chg% | `(LTP − R4) / R4 × 100` — how far above trigger |
| Refresh | Every 3 minutes (configurable in sidebar) |

---

## 📋 Table Columns

| Column | Description |
|--------|-------------|
| Symbol | Stock name + Strike + CE/PE |
| Open | Option open price of the day |
| LTP | Current last traded price |
| R4 | Camarilla R4 level (trigger price) |
| Chg% | % move above R4 trigger |
| Vol | Total volume traded |
| Ctr | Approx contracts (Vol ÷ Lot size) |

---

## ⚠️ Important Notes

- **Access token expires daily** — refresh before 9:15 AM IST
- Kite Connect API has rate limits; scanning 180 stocks takes ~60–90 seconds
- Historical data API charges may apply on Kite Connect (check your plan)
- This is for **educational/informational purposes only**, not financial advice
