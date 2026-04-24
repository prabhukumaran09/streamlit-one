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
    background:#0a1120; border:1px solid #1e3a5f;
    border-radius:6px; padding:8px 14px; flex:1; text-align:center;
}
.metric-label { font-size:0.6rem; color:#546e7a; letter-spacing:2px; text-transform:uppercase; margin-bottom:3px; }
.metric-value { font-family:'JetBrains Mono',monospace; font-size:1.2rem; font-weight:700; }
.c-ce      { color:#00e676; }
.c-pe      { color:#ff5252; }
.c-near    { color:#ffd740; }
.c-total   { color:#4fc3f7; }
.c-neutral { color:#90a4ae; font-size:0.95rem !important; }

/* ── Section labels ── */
.sec-hdr {
    padding:5px 14px; border-radius:4px;
    font-family:'Rajdhani',sans-serif;
    font-size:0.95rem; font-weight:700;
    letter-spacing:2px; text-transform:uppercase;
    margin-bottom:6px; margin-top:10px;
}
.hdr-ce-break  { background:linear-gradient(90deg,#002200,#0a150a); border-left:3px solid #00e676; color:#00e676; }
.hdr-pe-break  { background:linear-gradient(90deg,#220000,#150a0a); border-left:3px solid #ff5252; color:#ff5252; }
.hdr-ce-near   { background:linear-gradient(90deg,#1a1500,#120f00); border-left:3px solid #ffd740; color:#ffd740; }
.hdr-pe-near   { background:linear-gradient(90deg,#1a1500,#120f00); border-left:3px solid #ffab40; color:#ffab40; }

/* ── Divider ── */
.divider { border:none; border-top:1px solid #1e3a5f; margin:8px 0; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border:1px solid #1e3a5f !important; border-radius:6px !important; overflow:hidden; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background:#07090f !important; border-right:1px solid #1e3a5f; }
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stNumberInput input,
section[data-testid="stSidebar"] .stSelectbox div {
    background:#0a1120 !important; color:#c8d6e5 !important;
    border:1px solid #1e3a5f !important; font-family:'JetBrains Mono',monospace;
}
section[data-testid="stSidebar"] label {
    color:#78909c !important; font-size:0.75rem; letter-spacing:1px; text-transform:uppercase;
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
@st.cache_data(ttl=86400)
def fetch_instruments(_kite):
    """
    Returns NFO instrument DataFrame AND the live F&O stock universe.
    F&O stocks = unique `name` values in NFO-OPT segment (stock options only,
    excludes NIFTY/BANKNIFTY index options).
    """
    try:
        nfo_df = pd.DataFrame(_kite.instruments("NFO"))
        if nfo_df.empty:
            return nfo_df, []
        # Stock options only: segment=NFO-OPT, instrument_type CE/PE, name not an index
        INDEX_NAMES = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX",
                       "BANKEX", "NIFTYNXT50", "NIFTY50", "CNXFINANCE"}
        opt_stocks = nfo_df[
            (nfo_df["segment"] == "NFO-OPT") &
            (nfo_df["instrument_type"].isin(["CE", "PE"])) &
            (~nfo_df["name"].isin(INDEX_NAMES))
        ]["name"].dropna().unique().tolist()
        fno_universe = sorted(opt_stocks)
        return nfo_df, fno_universe
    except Exception as e:
        st.error(f"Instrument fetch error: {e}")
        return pd.DataFrame(), []

# ─────────────────────────────────────────────
# FNO_STOCKS — loaded dynamically at runtime
# Falls back to empty list before first kite init
# ─────────────────────────────────────────────
if "fno_stocks" not in st.session_state:
    st.session_state["fno_stocks"] = []

def get_fno_stocks(kite) -> list:
    """Return cached F&O universe, fetching if needed."""
    if st.session_state["fno_stocks"]:
        return st.session_state["fno_stocks"]
    _, universe = fetch_instruments(kite)
    if universe:
        st.session_state["fno_stocks"] = universe
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
def scan_stock(kite, nfo_df: pd.DataFrame, symbol: str, trigger_cache: dict) -> dict:
    """
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

            # ── 5. 15-min candles ─────────────────────────────────────────
            to_dt   = datetime.now()
            from_dt = to_dt - timedelta(hours=3)
            try:
                hist = kite.historical_data(
                    instrument_token,
                    from_date=from_dt,
                    to_date=to_dt,
                    interval="15minute",
                )
            except Exception:
                continue

            if len(hist) < 2:
                continue

            last = hist[-2]   # last COMPLETED candle
            r4   = camarilla_r4(last["high"], last["low"], last["close"])
            if r4 <= 0:
                continue

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
def run_full_scan(kite, stocks: list, trigger_cache: dict) -> dict:
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
        stock_result = scan_stock(kite, nfo_df, symbol, trigger_cache)
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
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

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
    res = run_full_scan(kite, fno_stocks, st.session_state.trigger_cache)
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
    <div class="clock-label">IST &nbsp; <span class="pill-live">● LIVE</span></div>
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
    st.rerun()

if scan_now:
    if not kite:
        st.error("⚠️  Please enter your Kite API Key and Access Token in the credentials panel above.")
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
# AUTO-REFRESH
# ─────────────────────────────────────────────
if st.session_state.last_scan and kite:
    elapsed   = (now_ist() - st.session_state.last_scan).total_seconds()
    wait_secs = refresh_mins * 60
    remaining = int(wait_secs - elapsed)

    if remaining <= 0:
        do_scan()
        st.rerun()
    else:
        st.caption(f"⏱ Next auto-refresh in {remaining // 60}m {remaining % 60}s  (IST)")
        time.sleep(min(30, remaining))
        st.rerun()
