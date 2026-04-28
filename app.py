import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
import pytz

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Intraday Option Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="auto",
)

IST = pytz.timezone("Asia/Kolkata")

def now_ist() -> datetime:
    return datetime.now(IST)

def ist_str(fmt="%H:%M:%S") -> str:
    return now_ist().strftime(fmt)

# ─────────────────────────────────────────────
# MARKET HOURS HELPER
# ─────────────────────────────────────────────
MARKET_OPEN  = (9,  15)   # 9:15 AM IST
MARKET_CLOSE = (15, 30)   # 3:30 PM IST

def is_market_open() -> bool:
    """Returns True if current IST time is within NSE trading hours (Mon–Fri, 9:15–15:30)."""
    now = now_ist()
    if now.weekday() >= 5:          # Saturday=5, Sunday=6
        return False
    t = (now.hour, now.minute)
    return MARKET_OPEN <= t <= MARKET_CLOSE

def market_status() -> tuple[bool, str]:
    """Returns (is_open, status_message)."""
    now = now_ist()
    if now.weekday() >= 5:
        return False, "🔴 Market Closed — Weekend"
    t = (now.hour, now.minute)
    if t < MARKET_OPEN:
        opens_in = (MARKET_OPEN[0] * 60 + MARKET_OPEN[1]) - (now.hour * 60 + now.minute)
        return False, f"🟡 Pre-Market — Opens in {opens_in} min"
    if t > MARKET_CLOSE:
        return False, "🔴 Market Closed — After Hours (15:30 IST)"
    mins_left = (MARKET_CLOSE[0] * 60 + MARKET_CLOSE[1]) - (now.hour * 60 + now.minute)
    return True, f"🟢 Market Open — Closes in {mins_left} min"

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Rajdhani:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif;
    background-color: #07090f !important;
    color: #c8d6e5 !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0.6rem 1rem 1rem 1rem !important; max-width: 100% !important; }

/* ── Top bar ── */
.top-bar {
    background: linear-gradient(90deg,#0a1628 0%,#0d2040 50%,#0a1628 100%);
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 10px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}
.app-title {
    font-size: 1.55rem; font-weight: 700; color: #4fc3f7;
    letter-spacing: 3px; text-transform: uppercase;
}
.app-subtitle {
    font-size: 0.7rem; color: #546e7a;
    letter-spacing: 2px; text-transform: uppercase; margin-top: 2px;
}
.live-clock {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.4rem; font-weight: 700; color: #ffd740;
    background: #0d1b2a; padding: 6px 18px;
    border-radius: 6px; border: 1px solid #3d3000;
    letter-spacing: 2px;
}
.clock-label {
    font-size: 0.6rem; color: #78909c; letter-spacing: 2px;
    text-transform: uppercase; text-align: center; margin-top: 2px;
}
.last-scan-ts {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem; color: #26a69a;
    background: #051a14; padding: 4px 12px;
    border-radius: 4px; border: 1px solid #0d3d2e;
}

/* ── Metric row ── */
.metric-row { display:flex; gap:8px; margin-bottom:10px; }
.metric-card {
    background: linear-gradient(145deg, #1a2744 0%, #162038 100%) !important;
    border: 1px solid #2e4a7a !important;
    border-radius: 8px !important; padding: 10px 16px !important; flex:1; text-align:center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4) !important;
}
.metric-label {
    font-size:0.68rem !important; color:#a0b8d8 !important;
    letter-spacing:2px; text-transform:uppercase; margin-bottom:4px;
    font-weight: 600 !important;
}
.metric-value { font-family:'JetBrains Mono',monospace; font-size:1.25rem !important; font-weight:700 !important; }
.c-ce      { color:#00ff88 !important; text-shadow: 0 0 8px rgba(0,255,136,0.4); }
.c-pe      { color:#ff6b6b !important; text-shadow: 0 0 8px rgba(255,107,107,0.4); }
.c-near    { color:#ffd740 !important; text-shadow: 0 0 8px rgba(255,215,64,0.3); }
.c-total   { color:#64d8ff !important; text-shadow: 0 0 8px rgba(100,216,255,0.3); }
.c-neutral { color:#d0e0f0 !important; font-size:0.95rem !important; font-weight:600 !important; }

/* ── Section labels ── */
.sec-hdr {
    padding:6px 16px !important; border-radius:6px !important;
    font-family:'Rajdhani',sans-serif !important;
    font-size:0.95rem !important; font-weight:700 !important;
    letter-spacing:2px; text-transform:uppercase;
    margin-bottom:6px; margin-top:10px;
}
.hdr-ce-break  { background:linear-gradient(90deg,#003d1a,#001a0c) !important; border-left:3px solid #00ff88 !important; color:#00ff88 !important; }
.hdr-pe-break  { background:linear-gradient(90deg,#3d0000,#1a0000) !important; border-left:3px solid #ff6b6b !important; color:#ff6b6b !important; }
.hdr-ce-near   { background:linear-gradient(90deg,#3d3000,#1a1500) !important; border-left:3px solid #ffd740 !important; color:#ffd740 !important; }
.hdr-pe-near   { background:linear-gradient(90deg,#3d3000,#1a1500) !important; border-left:3px solid #ffab40 !important; color:#ffab40 !important; }

/* ── Divider ── */
.divider { border:none; border-top:1px solid #2e4a7a; margin:8px 0; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border:1px solid #2e4a7a !important; border-radius:6px !important; overflow:hidden; }

/* ════════════════════════════════════════════
   SIDEBAR — HIGH CONTRAST
   ════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: #0f1e35 !important;
    border-right: 2px solid #2e4a7a !important;
}
/* All text inside sidebar */
section[data-testid="stSidebar"] * {
    color: #c8dff5 !important;
}
/* Page nav links */
section[data-testid="stSidebar"] a {
    color: #64d8ff !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-decoration: none !important;
}
section[data-testid="stSidebar"] a:hover {
    color: #ffffff !important;
    background: rgba(100,216,255,0.12) !important;
    border-radius: 6px;
}
/* Active page */
section[data-testid="stSidebar"] [aria-current="page"],
section[data-testid="stSidebar"] [aria-selected="true"] {
    background: rgba(100,216,255,0.15) !important;
    border-radius: 6px !important;
    color: #ffffff !important;
}
/* Scanner Info title */
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h1 {
    color: #64d8ff !important;
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: 2px !important;
    font-weight: 700 !important;
}
/* Info text / caption */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #b0c8e8 !important;
    font-size: 0.82rem !important;
    line-height: 1.6 !important;
}
/* Bold text inside captions */
section[data-testid="stSidebar"] strong {
    color: #ffd740 !important;
    font-weight: 700 !important;
}
/* Inputs */
section[data-testid="stSidebar"] input {
    background: #1a2d48 !important;
    color: #e0eeff !important;
    border: 1px solid #2e4a7a !important;
}
section[data-testid="stSidebar"] label {
    color: #a0c0e0 !important;
    font-size: 0.78rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    font-weight: 600 !important;
}

/* ── Buttons ── */
.stButton > button {
    background:#0a1628 !important; color:#4fc3f7 !important;
    border:1px solid #1e3a5f !important; border-radius:4px !important;
    font-family:'Rajdhani',sans-serif !important; font-weight:600 !important;
    letter-spacing:1px; text-transform:uppercase; transition:all 0.2s;
}
.stButton > button:hover { background:#1b4f72 !important; border-color:#4fc3f7 !important; }

/* ── Live pill ── */
.pill-live {
    display:inline-block; background:#002200; color:#00e676;
    border:1px solid #00e676; padding:2px 10px; border-radius:12px;
    font-size:0.65rem; letter-spacing:2px; font-weight:700;
    animation:blink 2s infinite; text-transform:uppercase;
}
.pill-closed {
    display:inline-block; background:#1a0000; color:#ff5252;
    border:1px solid #ff5252; padding:2px 10px; border-radius:12px;
    font-size:0.65rem; letter-spacing:1px; font-weight:700;
    text-transform:uppercase;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }

/* ── Near-breakout row yellow tint via caption ── */
.near-note { font-size:0.72rem; color:#ffd740; margin-bottom:4px; letter-spacing:1px; }

/* ── Credential panel ── */
.cred-panel {
    background: linear-gradient(135deg, #0a1628 0%, #0d1f3c 100%);
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 22px 28px 18px 28px;
    margin-bottom: 14px;
}
.cred-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1rem; font-weight: 700; color: #4fc3f7;
    letter-spacing: 2px; text-transform: uppercase;
    margin-bottom: 14px;
    display: flex; align-items: center; gap: 8px;
}
.cred-saved {
    background: #002a1a; border: 1px solid #00c853;
    border-radius: 8px; padding: 10px 18px;
    color: #00e676; font-size: 0.85rem;
    font-family: 'JetBrains Mono', monospace;
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 10px;
}
.settings-row {
    background: #0a1120; border: 1px solid #1e3a5f;
    border-radius: 8px; padding: 14px 20px;
    margin-bottom: 10px;
    display: flex; gap: 30px; align-items: center; flex-wrap: wrap;
}
.settings-label {
    font-size: 0.65rem; color: #546e7a; letter-spacing: 2px;
    text-transform: uppercase; margin-bottom: 3px;
}
/* Style streamlit text inputs to match terminal theme */
div[data-testid="stTextInput"] input {
    background: #040810 !important;
    color: #c8d6e5 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #4fc3f7 !important;
    box-shadow: 0 0 0 1px #4fc3f7 !important;
}
div[data-testid="stTextInput"] label {
    color: #78909c !important;
    font-size: 0.72rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    font-family: 'Rajdhani', sans-serif !important;
}
div[data-testid="stSelectbox"] label,
div[data-testid="stNumberInput"] label {
    color: #78909c !important;
    font-size: 0.72rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}
</style>
""", unsafe_allow_html=True)

import os

# ─────────────────────────────────────────────
# CREDENTIAL RESOLVER
# Priority: st.secrets → env vars → session state
# ─────────────────────────────────────────────
def _resolve(secret_key: str, session_key: str) -> str:
    try:
        val = st.secrets.get(secret_key, "")
        if val:
            return val
    except Exception:
        pass
    val = os.environ.get(secret_key, "")
    if val:
        return val
    return st.session_state.get(session_key, "")

def get_credentials():
    return _resolve("KITE_API_KEY", "api_key"), _resolve("KITE_ACCESS_TOKEN", "access_token")

def creds_source() -> str:
    try:
        if st.secrets.get("KITE_API_KEY", ""):
            return "secrets"
    except Exception:
        pass
    if os.environ.get("KITE_API_KEY", ""):
        return "env"
    if st.session_state.get("api_key", ""):
        return "manual"
    return "none"

# ─────────────────────────────────────────────
# KITE CONNECT  (not cached — so daily token
# updates in Secrets dashboard take effect immediately)
# ─────────────────────────────────────────────
def get_kite():
    try:
        from kiteconnect import KiteConnect
        api_key, access_token = get_credentials()
        if not all([api_key, access_token]):
            return None
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        return kite
    except Exception:
        return None

# ─────────────────────────────────────────────
# F&O UNIVERSE
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# CAMARILLA R4
# ─────────────────────────────────────────────
def camarilla_r4(high: float, low: float, close: float) -> float:
    return close + (high - low) * 1.1 / 2

# ─────────────────────────────────────────────
# INSTRUMENTS + LIVE F&O UNIVERSE
# Fetched directly from Kite — always accurate,
# never needs manual updates.
# Cached for 1 hour so it refreshes once per session.
# ─────────────────────────────────────────────
@st.cache_resource(ttl=86400)
def _load_instruments_cached(api_key: str, access_token: str):
    """
    Fetches NFO instruments using explicit string args so
    cache_resource can hash them reliably.
    Cached 24hrs across ALL sessions — fetched only once per deploy.
    Returns (nfo_df, fno_universe_list).
    """
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        nfo_df = pd.DataFrame(kite.instruments("NFO"))
        if nfo_df.empty:
            return pd.DataFrame(), []
        INDEX_NAMES = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX",
                       "BANKEX", "NIFTYNXT50", "NIFTY50", "CNXFINANCE"}
        opt_stocks = nfo_df[
            (nfo_df["segment"] == "NFO-OPT") &
            (nfo_df["instrument_type"].isin(["CE", "PE"])) &
            (~nfo_df["name"].isin(INDEX_NAMES))
        ]["name"].dropna().unique().tolist()
        return nfo_df, sorted(opt_stocks)
    except Exception as e:
        st.error(f"Instrument fetch error: {e}")
        return pd.DataFrame(), []

def fetch_instruments(kite):
    """Returns (nfo_df, fno_universe_list). Uses persistent cache."""
    api_key, access_token = get_credentials()
    return _load_instruments_cached(api_key, access_token)

def get_fno_stocks(kite) -> list:
    """Return live F&O universe. Persistent across sessions."""
    _, universe = fetch_instruments(kite)
    return universe

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def nearest_expiry(expiries):
    today = now_ist().date()
    future = [e for e in expiries if e >= today]
    return min(future) if future else None

def get_atm_strike(price: float, step: float) -> float:
    return round(round(price / step) * step, 2)

# ─────────────────────────────────────────────
# TODAY'S STOCK OPEN (ATM REFERENCE)  ← key change
# ─────────────────────────────────────────────
def get_stock_open(kite, symbol: str):
    """Today's open price of the underlying NSE stock — used as ATM reference."""
    try:
        q = kite.quote(f"NSE:{symbol}")
        return q[f"NSE:{symbol}"]["ohlc"]["open"]
    except Exception:
        return None

# ─────────────────────────────────────────────
# SCAN ONE STOCK
# Returns breakout rows AND near-breakout rows
# ─────────────────────────────────────────────
def get_prev_trading_day():
    """Get previous trading day (skip weekends)."""
    prev = now_ist().date() - timedelta(days=1)
    while prev.weekday() >= 5:  # Skip Saturday=5, Sunday=6
        prev -= timedelta(days=1)
    return prev

def scan_stock(kite, nfo_df: pd.DataFrame, symbol: str, trigger_cache: dict, r4_cache: dict) -> dict:
    """
    R4 Strategy:
    - R4 is calculated ONCE per option per day using PREVIOUS day's last 15-min candle
    - R4 remains constant throughout the trading day
    - Cached in r4_cache with key = tradingsymbol
    
    Returns:
        {
          "CE": {"breakout": [...], "near": [...]},
          "PE": {"breakout": [...], "near": [...]},
        }
    """
    out = {"CE": {"breakout": [], "near": []}, "PE": {"breakout": [], "near": []}}

    try:
        # ── 1. Today's stock open → ATM reference ─────────────────────────
        stock_open = get_stock_open(kite, symbol)
        if not stock_open:
            return out

        # ── 2. Filter NFO options ─────────────────────────────────────────
        sym_opt = nfo_df[
            (nfo_df["name"] == symbol) &
            (nfo_df["segment"] == "NFO-OPT")
        ].copy()
        if sym_opt.empty:
            return out

        sym_opt["expiry"] = pd.to_datetime(sym_opt["expiry"]).dt.date
        expiry = nearest_expiry(sym_opt["expiry"].unique().tolist())
        if not expiry:
            return out

        exp_opt = sym_opt[sym_opt["expiry"] == expiry]
        strikes = sorted(exp_opt["strike"].unique())
        if len(strikes) < 2:
            return out
        strike_step = strikes[1] - strikes[0]

        # ── 3. ATM strike from today's stock open ─────────────────────────
        atm = get_atm_strike(stock_open, strike_step)

        # ── 4. CE and PE ──────────────────────────────────────────────────
        for opt_type in ["CE", "PE"]:
            opt_row = exp_opt[
                (exp_opt["strike"] == atm) &
                (exp_opt["instrument_type"] == opt_type)
            ]
            if opt_row.empty:
                continue

            tradingsymbol    = opt_row.iloc[0]["tradingsymbol"]
            instrument_token = int(opt_row.iloc[0]["instrument_token"])
            cache_key        = tradingsymbol

            # ── 5. Get or Calculate R4 (FIXED for entire day) ────────────
            if cache_key in r4_cache:
                # R4 already calculated for today — use cached value
                r4 = r4_cache[cache_key]
            else:
                # Calculate R4 from PREVIOUS day's last 15-min candle
                prev_day = get_prev_trading_day()
                prev_from = datetime.combine(prev_day, datetime.min.time())
                prev_to   = datetime.combine(prev_day, datetime.max.time())
                
                try:
                    prev_candles = kite.historical_data(
                        instrument_token,
                        from_date=prev_from,
                        to_date=prev_to,
                        interval="15minute"
                    )
                except Exception:
                    continue

                if not prev_candles:
                    # No previous day data — try using today's first candle as fallback
                    # (e.g., new option listings, first day of expiry)
                    now_ist_dt = now_ist()
                    today_from = now_ist_dt.replace(hour=9, minute=0, second=0, microsecond=0)
                    try:
                        today_candles = kite.historical_data(
                            instrument_token,
                            from_date=today_from,
                            to_date=now_ist_dt,
                            interval="15minute"
                        )
                        if len(today_candles) < 2:
                            continue  # Not enough data yet
                        last = today_candles[-2]  # Last completed candle today
                    except Exception:
                        continue
                else:
                    # Use previous day's last candle
                    last = prev_candles[-1]

                r4 = camarilla_r4(last["high"], last["low"], last["close"])
                if r4 <= 0:
                    continue
                
                # Cache R4 for rest of the day
                r4_cache[cache_key] = r4

            # ── 6. Current LTP ────────────────────────────────────────────
            try:
                q    = kite.quote(f"NFO:{tradingsymbol}")
                info = q[f"NFO:{tradingsymbol}"]
                ltp  = info["last_price"]
            except Exception:
                continue

            # ── 7. Classify ───────────────────────────────────────────────
            now_str = ist_str()

            # Near-breakout threshold: LTP >= R4 * (1 - 0.20)  i.e. within 20% below R4
            near_threshold = r4 * 0.80

            if ltp > r4:
                # ── BREAKOUT ──
                chg_pct = round(((ltp - r4) / r4) * 100, 2)

                # Record trigger time once; never overwrite
                if cache_key not in trigger_cache:
                    trigger_cache[cache_key] = now_str

                out[opt_type]["breakout"].append({
                    "Symbol":        tradingsymbol,
                    "Open":          round(stock_open, 2),
                    "LTP":           round(ltp, 2),
                    "R4":            round(r4, 2),
                    "Chg%":          f"+{chg_pct}%",
                    "Trigger Time":  trigger_cache[cache_key],
                    "_chg_val":      chg_pct,
                    "_status":       "breakout",
                })

            elif ltp >= near_threshold:
                # ── NEAR BREAKOUT ──
                # Gap% = how far below R4 (negative value)
                gap_pct = round(((ltp - r4) / r4) * 100, 2)  # will be negative

                # Clear trigger cache — not broken out yet
                trigger_cache.pop(cache_key, None)

                out[opt_type]["near"].append({
                    "Symbol":        tradingsymbol,
                    "Open":          round(stock_open, 2),
                    "LTP":           round(ltp, 2),
                    "R4":            round(r4, 2),
                    "Gap to R4":     f"{gap_pct}%",
                    "_gap_val":      gap_pct,   # negative; closer to 0 = nearer to breakout
                    "_status":       "near",
                })

            else:
                # Fully below near-threshold — reset trigger cache
                trigger_cache.pop(cache_key, None)

    except Exception:
        pass

    return out

# ─────────────────────────────────────────────
# FULL SCAN
# ─────────────────────────────────────────────
def run_full_scan(kite, stocks: list, trigger_cache: dict, r4_cache: dict) -> dict:
    """
    Returns:
        {
          "CE": {"breakout": [...], "near": [...]},
          "PE": {"breakout": [...], "near": [...]},
        }
    All breakout lists sorted by Chg% desc; near lists sorted by Gap desc (nearest first).
    """
    nfo_df, _ = fetch_instruments(kite)
    if nfo_df.empty:
        return _empty_result()

    result = {"CE": {"breakout": [], "near": []},
              "PE": {"breakout": [], "near": []}}

    progress = st.progress(0, text="Initialising scan…")
    total = len(stocks)

    for idx, symbol in enumerate(stocks):
        stock_result = scan_stock(kite, nfo_df, symbol, trigger_cache, r4_cache)
        for opt_type in ["CE", "PE"]:
            result[opt_type]["breakout"].extend(stock_result[opt_type]["breakout"])
            result[opt_type]["near"].extend(stock_result[opt_type]["near"])
        progress.progress((idx + 1) / total, text=f"Scanning {symbol}… ({idx+1}/{total})")

    progress.empty()

    # ── Sort ──────────────────────────────────────────────────────────────
    for opt_type in ["CE", "PE"]:
        # Breakouts: highest Chg% first
        result[opt_type]["breakout"].sort(key=lambda x: x["_chg_val"], reverse=True)
        # Near: closest to R4 first (least negative gap)
        result[opt_type]["near"].sort(key=lambda x: x["_gap_val"], reverse=True)

    return result

def _empty_result():
    return {"CE": {"breakout": [], "near": []}, "PE": {"breakout": [], "near": []}}

# ─────────────────────────────────────────────
# DISPLAY DFs
# ─────────────────────────────────────────────
BREAK_COLS = ["Symbol", "Open", "LTP", "R4", "Chg%", "Trigger Time"]
NEAR_COLS  = ["Symbol", "Open", "LTP", "R4", "Gap to R4"]

def make_break_df(rows): return pd.DataFrame(rows)[BREAK_COLS] if rows else pd.DataFrame(columns=BREAK_COLS)
def make_near_df(rows):  return pd.DataFrame(rows)[NEAR_COLS]  if rows else pd.DataFrame(columns=NEAR_COLS)

BREAK_CFG = {
    "Symbol":       st.column_config.TextColumn("Symbol",         width="large"),
    "Open":         st.column_config.NumberColumn("Open",         format="%.2f"),
    "LTP":          st.column_config.NumberColumn("LTP",          format="%.2f"),
    "R4":           st.column_config.NumberColumn("R4 (Trigger)", format="%.2f"),
    "Chg%":         st.column_config.TextColumn("Chg%",           width="small"),
    "Trigger Time": st.column_config.TextColumn("Trigger Time",   width="small"),
}
NEAR_CFG = {
    "Symbol":    st.column_config.TextColumn("Symbol",      width="large"),
    "Open":      st.column_config.NumberColumn("Open",      format="%.2f"),
    "LTP":       st.column_config.NumberColumn("LTP",       format="%.2f"),
    "R4":        st.column_config.NumberColumn("R4",        format="%.2f"),
    "Gap to R4": st.column_config.TextColumn("Gap to R4",  width="small"),
}

def render_table(df, cfg, empty_msg="—"):
    if df.empty:
        st.caption(empty_msg)
    else:
        st.dataframe(
            df, use_container_width=True, hide_index=True,
            height=min(55 + len(df) * 36, 560),
            column_config=cfg,
        )

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
defaults = {
    "scan_result":   _empty_result(),
    "last_scan":     None,
    "api_key":       "",
    "api_secret":    "",
    "access_token":  "",
    "trigger_cache": {},
    "r4_cache":      {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# AUTO-CLEAR R4 CACHE ON NEW TRADING DAY
# R4 values should be recalculated fresh each day
# ─────────────────────────────────────────────
if "r4_cache_date" not in st.session_state:
    st.session_state.r4_cache_date = None

current_date = now_ist().date()
if st.session_state.r4_cache_date != current_date:
    # New trading day detected — clear R4 cache
    st.session_state.r4_cache = {}
    st.session_state.r4_cache_date = current_date

# ─────────────────────────────────────────────
# INLINE CREDENTIAL PANEL
# ─────────────────────────────────────────────
_src = creds_source()
_api_key, _access_token = get_credentials()
_has_creds = bool(_api_key and _access_token)

_source_labels = {
    "secrets": ("🟢", "Loaded from Streamlit Secrets / secrets.toml"),
    "env":     ("🟡", "Loaded from environment variables"),
    "manual":  ("🔵", "Entered manually in this session"),
    "none":    ("🔴", "No credentials found"),
}
_icon, _src_label = _source_labels.get(_src, ("🔴", "Unknown"))
_masked_key = (_api_key[:6] + "••••••") if _api_key else "—"

if _has_creds:
    # Compact status bar when credentials are present
    st.markdown(f'''
    <div class="cred-saved">
      {_icon} &nbsp;<strong>Kite Connect: {_src_label}</strong>
      &nbsp;|&nbsp; API Key: <code>{_masked_key}</code>
      &nbsp;|&nbsp; ✅ Access token set
    </div>''', unsafe_allow_html=True)
    with st.expander("🔄 Override credentials manually (optional)", expanded=False):
        st.caption("Only needed if you want to test with different credentials. Secrets/env values take priority on next restart.")
        oc1, oc2, oc3 = st.columns(3)
        with oc1:
            st.session_state.api_key = st.text_input("API Key", value=st.session_state.api_key, type="password", key="ovr_key")
        with oc2:
            st.session_state.api_secret = st.text_input("API Secret", value=st.session_state.api_secret, type="password", key="ovr_secret")
        with oc3:
            st.session_state.access_token = st.text_input("Access Token", value=st.session_state.access_token, type="password", key="ovr_token")
else:
    # No credentials found — show input panel
    st.markdown('<div class="cred-panel">', unsafe_allow_html=True)
    st.markdown('<div class="cred-title">🔑 &nbsp;Zerodha Kite Connect — Enter Credentials</div>', unsafe_allow_html=True)
    st.caption("💡 Tip: Configure secrets in Streamlit Cloud dashboard so you only update the access token once daily — no re-entry needed.")
    cred_c1, cred_c2, cred_c3 = st.columns(3)
    with cred_c1:
        st.session_state.api_key = st.text_input(
            "API Key", value=st.session_state.api_key,
            placeholder="Your Kite API Key", type="password"
        )
    with cred_c2:
        st.session_state.api_secret = st.text_input(
            "API Secret", value=st.session_state.api_secret,
            placeholder="Your Kite API Secret", type="password"
        )
    with cred_c3:
        st.session_state.access_token = st.text_input(
            "Access Token", value=st.session_state.access_token,
            placeholder="Today's Access Token (refresh daily before 9:15 AM IST)", type="password"
        )
    st.caption("🔒 Credentials are stored only in your browser session and never sent anywhere except Zerodha's API.")
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SETTINGS ROW (inline, always visible)
# ─────────────────────────────────────────────
set_c1, set_c2, set_c3, set_c4 = st.columns([1, 1, 1, 5])
with set_c1:
    refresh_mins = st.selectbox("Auto-refresh (mins)", [3, 5, 10, 15], index=0)
with set_c2:
    near_pct = st.number_input("Near R4 threshold %", min_value=5, max_value=40, value=20, step=5,
                               help="Show options whose LTP is within X% below R4")
with set_c3:
    min_chg = st.number_input("Min breakout Chg%", min_value=0.0, value=0.0, step=10.0)

# Keep sidebar minimal / hidden
with st.sidebar:
    st.markdown("### ℹ️ Scanner Info")
    st.caption(
        "**ATM** = nearest strike to today's stock open\n\n"
        "**R4** = Close + (H−L)×1.1/2\n\n"
        "*(last completed 15-min candle of option)*\n\n"
        "**Breakout** → LTP > R4\n\n"
        "**Near R4** → LTP within threshold% below R4\n\n"
        "**Chg%** = (LTP−R4)/R4 × 100\n\n"
        "**Trigger Time** = IST when LTP first crossed R4"
    )

# ─────────────────────────────────────────────
# KITE OBJECT + CONNECTION TEST
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# KITE CONNECTION TEST
# ─────────────────────────────────────────────
def test_kite_connection(kite) -> tuple[bool, str]:
    """
    Verifies Kite connection is alive and access token is valid.
    Returns (ok: bool, message: str)
    """
    if kite is None:
        return False, "❌ No credentials found. Please enter your API Key and Access Token."
    try:
        profile = kite.profile()
        name = profile.get("user_name", "User")
        return True, f"✅ Connected as **{name}**"
    except Exception as e:
        err = str(e).lower()
        if "token" in err or "invalid" in err or "expired" in err or "unauthorised" in err or "unauthorized" in err:
            return False, (
                "🔴 **Access token is invalid or expired.**\n\n"
                "Your Kite access token expires daily at midnight IST. "
                "Please run `token_refresh_mobile.py`, copy the new token, "
                "and update it in **Streamlit Cloud → Settings → Secrets** "
                "(`KITE_ACCESS_TOKEN = \"new_token\"`)."
            )
        elif "api_key" in err or "key" in err:
            return False, "🔴 **Invalid API Key.** Please check your Kite API Key in credentials."
        elif "network" in err or "connection" in err or "timeout" in err:
            return False, "🔴 **Network error.** Could not reach Zerodha servers. Check your internet connection."
        else:
            return False, f"🔴 **Kite connection failed:** {e}"

kite = get_kite()

# Show connection status banner
if kite is not None:
    _conn_ok, _conn_msg = test_kite_connection(kite)
    if not _conn_ok:
        st.error(_conn_msg)
        st.stop()          # halt page — no scan possible with bad token

# ─────────────────────────────────────────────
# SCAN EXECUTOR
# ─────────────────────────────────────────────
def do_scan():
    fno_stocks = get_fno_stocks(kite)
    res = run_full_scan(kite, fno_stocks, st.session_state.trigger_cache, st.session_state.r4_cache)
    # Apply min Chg% filter on breakouts
    if min_chg > 0:
        for t in ["CE", "PE"]:
            res[t]["breakout"] = [r for r in res[t]["breakout"] if r["_chg_val"] >= min_chg]
    # Apply configurable near threshold
    threshold = near_pct / 100
    for t in ["CE", "PE"]:
        res[t]["near"] = [
            r for r in res[t]["near"]
            if r["_gap_val"] >= -(threshold * 100)
        ]
    st.session_state.scan_result = res
    st.session_state.last_scan   = now_ist()

# ─────────────────────────────────────────────
# ── TOP BAR  (live clock + last scan time) ───
# We use st.empty() so only the clock div re-renders
# ─────────────────────────────────────────────
clock_ph   = st.empty()
last_upd   = st.session_state.last_scan.strftime("%d %b %Y  %H:%M:%S IST") \
             if st.session_state.last_scan else "—"
_mkt_open, _mkt_msg = market_status()
_pill_cls  = "pill-live" if _mkt_open else "pill-closed"
clock_ph.markdown(f"""
<div class="top-bar">
  <div>
    <div class="app-title">📈 Intraday Option Scanner</div>
    <div class="app-subtitle">
      Camarilla R4 Breakout &nbsp;·&nbsp; ATM via Today's Stock Open
      &nbsp;·&nbsp; F&amp;O Universe &nbsp;·&nbsp; 15-Min Candles &nbsp;·&nbsp; IST
    </div>
  </div>
  <div style="text-align:center;">
    <div class="live-clock" id="ist-clock">{ist_str("%H:%M:%S")}</div>
    <div class="clock-label">IST &nbsp; <span class="{_pill_cls}">{_mkt_msg}</span></div>
  </div>
  <div style="text-align:right;">
    <div style="font-size:0.6rem;color:#546e7a;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;">Last Scan</div>
    <div class="last-scan-ts">{last_upd}</div>
  </div>
</div>
<script>
(function(){{
  function pad(n){{return n<10?"0"+n:n;}}
  function tick(){{
    var d=new Date();
    var ist=new Date(d.toLocaleString("en-US",{{timeZone:"Asia/Kolkata"}}));
    var t=pad(ist.getHours())+":"+pad(ist.getMinutes())+":"+pad(ist.getSeconds());
    var el=document.getElementById("ist-clock");
    if(el) el.innerText=t;
  }}
  tick();
  setInterval(tick,1000);
}})();
</script>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# METRIC CARDS
# ─────────────────────────────────────────────
res = st.session_state.scan_result
ce_break = len(res["CE"]["breakout"])
pe_break = len(res["PE"]["breakout"])
ce_near  = len(res["CE"]["near"])
pe_near  = len(res["PE"]["near"])

st.markdown(f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="metric-label">CE Breakouts</div>
    <div class="metric-value c-ce">{ce_break}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">PE Breakouts</div>
    <div class="metric-value c-pe">{pe_break}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">CE Near R4</div>
    <div class="metric-value c-near">{ce_near}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">PE Near R4</div>
    <div class="metric-value c-near">{pe_near}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Near Threshold</div>
    <div class="metric-value c-neutral">±{near_pct}%</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Universe</div>
    <div class="metric-value c-neutral">{len(get_fno_stocks(kite)) if kite else "—"} Stocks</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# BUTTONS
# ─────────────────────────────────────────────
c1, c2, c3 = st.columns([1, 1, 6])
with c1:
    scan_now  = st.button("⚡ Scan Now", use_container_width=True)
with c2:
    clear_btn = st.button("🗑 Clear",    use_container_width=True)

if clear_btn:
    st.session_state.scan_result   = _empty_result()
    st.session_state.last_scan     = None
    st.session_state.trigger_cache = {}
    st.session_state.r4_cache      = {}
    st.rerun()

if scan_now:
    if not kite:
        st.error("⚠️  Please enter your Kite API Key and Access Token in the credentials panel above.")
    elif not is_market_open():
        _, _status = market_status()
        st.warning(f"⚠️  {_status} — Live scan only runs between 9:15 AM and 3:30 PM IST on weekdays.")
    else:
        _ok, _msg = test_kite_connection(kite)
        if not _ok:
            st.error(_msg)
        else:
            with st.spinner("Running Camarilla R4 scan across F&O universe…"):
                do_scan()
            st.rerun()

# ─────────────────────────────────────────────
# GETTING-STARTED (before first scan)
# ─────────────────────────────────────────────
if not st.session_state.last_scan:
    st.info("""
**Getting Started**

1. Enter your **Kite API Key** and **Access Token** in the credentials panel above.
2. Click **⚡ Scan Now** to begin.
3. Results auto-refresh every **3 minutes** (configurable above).

**Logic**
- **ATM** = nearest strike to **today's stock open price**
- **R4** = `Close + (H−L) × 1.1/2` on last completed 15-min candle of ATM option
- 🟢 **Breakout** → LTP > R4 · sorted by Chg% descending
- 🟡 **Near R4** → LTP within 20% below R4 · sorted by closest to breakout first
- **Chg%** example: R4 = ₹16.95, LTP = ₹27 → Chg% = **+159.34%**
- All timestamps in **IST**
    """)

# ─────────────────────────────────────────────
# MAIN TABLES  (2 columns: CE | PE)
# ─────────────────────────────────────────────
left_col, right_col = st.columns(2)

with left_col:
    # ── CE Breakouts ──────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr hdr-ce-break">▲ CE Breakouts &nbsp;(Bullish)</div>', unsafe_allow_html=True)
    render_table(make_break_df(res["CE"]["breakout"]), BREAK_CFG,
                 empty_msg="No CE breakouts yet.")

    # ── CE Near R4 ────────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr hdr-ce-near">◈ CE Near R4 &nbsp;(Watch)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="near-note">⚡ LTP within {near_pct}% below R4 — approaching breakout</div>',
                unsafe_allow_html=True)
    render_table(make_near_df(res["CE"]["near"]), NEAR_CFG,
                 empty_msg="No CE options near R4.")

with right_col:
    # ── PE Breakouts ──────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr hdr-pe-break">▼ PE Breakouts &nbsp;(Bearish)</div>', unsafe_allow_html=True)
    render_table(make_break_df(res["PE"]["breakout"]), BREAK_CFG,
                 empty_msg="No PE breakouts yet.")

    # ── PE Near R4 ────────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr hdr-pe-near">◈ PE Near R4 &nbsp;(Watch)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="near-note">⚡ LTP within {near_pct}% below R4 — approaching breakout</div>',
                unsafe_allow_html=True)
    render_table(make_near_df(res["PE"]["near"]), NEAR_CFG,
                 empty_msg="No PE options near R4.")

# ─────────────────────────────────────────────
# AUTO-REFRESH  (only during market hours)
# ─────────────────────────────────────────────
_mkt_open_now, _mkt_status_now = market_status()

if not _mkt_open_now:
    # Outside market hours — show status, no refresh loop
    st.info(
        f"**{_mkt_status_now}**\n\n"
        "Auto-refresh is paused. The scanner will resume automatically "
        "when market opens at **9:15 AM IST** on the next trading day."
    )
elif st.session_state.last_scan and kite:
    # Inside market hours — normal refresh cycle
    elapsed   = (now_ist() - st.session_state.last_scan).total_seconds()
    wait_secs = refresh_mins * 60
    remaining = int(wait_secs - elapsed)

    if remaining <= 0:
        do_scan()
        st.rerun()
    else:
        st.caption(f"⏱ Next auto-refresh in {remaining // 60}m {remaining % 60}s  (IST) · Market closes at 15:30 IST")
        time.sleep(min(30, remaining))
        st.rerun()
