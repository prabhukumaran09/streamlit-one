import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import pytz
import os

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Backtest — Option Scanner",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

IST = pytz.timezone("Asia/Kolkata")

def now_ist():
    return datetime.now(IST)

def ist_time_str(dt):
    """Convert a naive or aware datetime to IST HH:MM string."""
    if dt is None:
        return "—"
    if hasattr(dt, "tzinfo") and dt.tzinfo is not None:
        dt = dt.astimezone(IST)
    return dt.strftime("%H:%M")

# ─────────────────────────────────────────────
# CSS — same dark terminal theme
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
.block-container { padding: 0.6rem 1.2rem 1rem 1.2rem !important; max-width: 100% !important; }

.bt-header {
    background: linear-gradient(90deg,#0a1628 0%,#1a0a28 50%,#0a1628 100%);
    border: 1px solid #3a1e5f;
    border-radius: 8px; padding: 12px 22px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 12px;
}
.bt-title {
    font-size: 1.5rem; font-weight: 700; color: #ce93d8;
    letter-spacing: 3px; text-transform: uppercase;
}
.bt-subtitle { font-size: 0.7rem; color: #6a4c7a; letter-spacing: 2px; text-transform: uppercase; margin-top:2px; }

/* ── Control panel ── */
.ctrl-panel {
    background: #0a1120; border: 1px solid #1e3a5f;
    border-radius: 8px; padding: 16px 22px; margin-bottom: 14px;
}

/* ── Summary cards ── */
.sum-row { display:flex; gap:8px; margin-bottom:12px; }
.sum-card {
    background:#0a1120; border:1px solid #2a1e4f;
    border-radius:6px; padding:8px 16px; flex:1; text-align:center;
}
.sum-label { font-size:0.6rem; color:#6a4c7a; letter-spacing:2px; text-transform:uppercase; margin-bottom:3px; }
.sum-value { font-family:'JetBrains Mono',monospace; font-size:1.2rem; font-weight:700; }
.c-purple  { color:#ce93d8; }
.c-green   { color:#00e676; }
.c-red     { color:#ff5252; }
.c-yellow  { color:#ffd740; }
.c-blue    { color:#4fc3f7; }
.c-neutral { color:#90a4ae; font-size:0.9rem !important; }

/* ── Section headers ── */
.sec-hdr {
    padding:5px 14px; border-radius:4px; margin-bottom:6px; margin-top:8px;
    font-family:'Rajdhani',sans-serif; font-size:0.95rem; font-weight:700;
    letter-spacing:2px; text-transform:uppercase;
}
.hdr-ce { background:linear-gradient(90deg,#002200,#0a150a); border-left:3px solid #00e676; color:#00e676; }
.hdr-pe { background:linear-gradient(90deg,#220000,#150a0a); border-left:3px solid #ff5252; color:#ff5252; }

/* ── Progress note ── */
.progress-note { font-size:0.78rem; color:#546e7a; letter-spacing:1px; margin-bottom:6px; }

/* ── Input labels ── */
div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stDateInput"] label {
    color: #78909c !important; font-size:0.72rem !important;
    letter-spacing:1px !important; text-transform:uppercase !important;
    font-family:'Rajdhani',sans-serif !important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stDateInput"] input {
    background: #040810 !important; color: #c8d6e5 !important;
    border: 1px solid #1e3a5f !important; border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.85rem !important;
}
.stButton > button {
    background:#1a0a28 !important; color:#ce93d8 !important;
    border:1px solid #3a1e5f !important; border-radius:4px !important;
    font-family:'Rajdhani',sans-serif !important; font-weight:600 !important;
    letter-spacing:1px; text-transform:uppercase; transition:all 0.2s; width:100%;
}
.stButton > button:hover { background:#3a1e5f !important; border-color:#ce93d8 !important; }

/* ── Credential saved bar ── */
.cred-saved {
    background:#002a1a; border:1px solid #00c853; border-radius:6px;
    padding:8px 16px; color:#00e676; font-size:0.82rem;
    font-family:'JetBrains Mono',monospace; margin-bottom:10px;
}
.cred-panel {
    background:linear-gradient(135deg,#0a1628,#0d1f3c);
    border:1px solid #1e3a5f; border-radius:10px;
    padding:18px 22px; margin-bottom:12px;
}
.cred-title {
    font-size:0.9rem; font-weight:700; color:#4fc3f7;
    letter-spacing:2px; text-transform:uppercase; margin-bottom:12px;
}

[data-testid="stDataFrame"] { border:1px solid #2a1e4f !important; border-radius:6px !important; overflow:hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CREDENTIAL RESOLVER (same as main app)
# ─────────────────────────────────────────────
def _resolve(secret_key, session_key):
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
# INSTRUMENTS + LIVE F&O UNIVERSE
# @st.cache_resource persists across reruns AND
# across users/sessions for the lifetime of the
# Streamlit worker — fetched only ONCE per deploy,
# not once per user session. Fastest possible.
# ─────────────────────────────────────────────
INDEX_NAMES = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX",
               "BANKEX", "NIFTYNXT50", "NIFTY50", "CNXFINANCE"}

@st.cache_resource(ttl=86400)
def _load_instruments_cached(api_key: str, access_token: str):
    """
    Fetches NFO instruments using explicit string args (not kite object)
    so cache_resource can hash them reliably.
    Cached for 24 hours across ALL sessions and reruns.
    Returns (nfo_df, fno_stocks_list).
    """
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        nfo_df = pd.DataFrame(kite.instruments("NFO"))
        if nfo_df.empty:
            return pd.DataFrame(), []
        opt_stocks = sorted(
            nfo_df[
                (nfo_df["segment"] == "NFO-OPT") &
                (nfo_df["instrument_type"].isin(["CE", "PE"])) &
                (~nfo_df["name"].isin(INDEX_NAMES))
            ]["name"].dropna().unique().tolist()
        )
        return nfo_df, opt_stocks
    except Exception as e:
        st.error(f"Instrument fetch error: {e}")
        return pd.DataFrame(), []

def fetch_instruments(kite):
    """Returns (nfo_df, fno_stocks_list). Uses persistent cache."""
    api_key, access_token = get_credentials()
    return _load_instruments_cached(api_key, access_token)

def get_fno_stocks(kite) -> list:
    """Returns live F&O stock universe as a sorted list."""
    _, stocks = fetch_instruments(kite)
    return stocks

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def camarilla_r4(high, low, close):
    return close + (high - low) * 1.1 / 2

def get_atm_strike(price, step):
    return round(round(price / step) * step, 2)

def nearest_expiry_for_date(expiries, ref_date):
    future = [e for e in expiries if e >= ref_date]
    return min(future) if future else None

# ─────────────────────────────────────────────
# PREV TRADING DAY  (skip weekends simply)
# ─────────────────────────────────────────────
def prev_trading_day(d: date) -> date:
    """Returns the previous calendar day skipping Saturday/Sunday."""
    prev = d - timedelta(days=1)
    while prev.weekday() >= 5:   # 5=Sat, 6=Sun
        prev -= timedelta(days=1)
    return prev

# ─────────────────────────────────────────────
# CORE BACKTEST LOGIC FOR ONE STOCK + DATE
# ─────────────────────────────────────────────
def backtest_stock(kite, nfo_df, symbol: str, bt_date: date) -> list:
    """
    For a given symbol and backtest date:
    1. Get stock open on bt_date  → ATM strike
    2. Get prev day's LAST 15-min candle of ATM option → R4
    3. Scan bt_date 15-min candles → find first breakout above R4
    4. Get option close price on bt_date
    5. Return result rows (CE and/or PE if breakout found)
    """
    rows = []
    try:
        # ── 1. Stock open on bt_date ──────────────────────────────────────
        from_dt  = datetime.combine(bt_date, datetime.min.time())
        to_dt    = from_dt + timedelta(hours=10)  # up to ~7:30pm covers full day
        try:
            # Get daily candle for bt_date to extract open
            nse_instruments = kite.instruments("NSE")
            nse_df = pd.DataFrame(nse_instruments)
            nse_row = nse_df[(nse_df["tradingsymbol"] == symbol) & (nse_df["segment"] == "NSE")]
            if nse_row.empty:
                return rows
            nse_token = int(nse_row.iloc[0]["instrument_token"])
            day_hist = kite.historical_data(nse_token, from_date=from_dt, to_date=to_dt, interval="day")
            if not day_hist:
                return rows
            stock_open = day_hist[0]["open"]
        except Exception:
            return rows

        # ── 2. NFO options for this symbol ───────────────────────────────
        sym_opt = nfo_df[
            (nfo_df["name"] == symbol) &
            (nfo_df["segment"] == "NFO-OPT")
        ].copy()
        if sym_opt.empty:
            return rows

        sym_opt["expiry"] = pd.to_datetime(sym_opt["expiry"]).dt.date
        # Use expiry that was valid on bt_date
        expiry = nearest_expiry_for_date(sym_opt["expiry"].unique().tolist(), bt_date)
        if not expiry:
            return rows

        exp_opt = sym_opt[sym_opt["expiry"] == expiry]
        strikes = sorted(exp_opt["strike"].unique())
        if len(strikes) < 2:
            return rows
        strike_step = strikes[1] - strikes[0]

        # ── 3. ATM strike ─────────────────────────────────────────────────
        atm = get_atm_strike(stock_open, strike_step)

        # ── 4. Previous trading day ───────────────────────────────────────
        prev_day = prev_trading_day(bt_date)
        prev_from = datetime.combine(prev_day, datetime.min.time())
        prev_to   = datetime.combine(prev_day, datetime.max.time())

        # ── 5. CE + PE ────────────────────────────────────────────────────
        for opt_type in ["CE", "PE"]:
            opt_row = exp_opt[
                (exp_opt["strike"] == atm) &
                (exp_opt["instrument_type"] == opt_type)
            ]
            if opt_row.empty:
                continue

            tradingsymbol    = opt_row.iloc[0]["tradingsymbol"]
            instrument_token = int(opt_row.iloc[0]["instrument_token"])

            # ── R4: from last 15-min candle of PREVIOUS day ───────────────
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
                continue

            last_prev = prev_candles[-1]   # last candle of previous day
            r4 = camarilla_r4(last_prev["high"], last_prev["low"], last_prev["close"])
            if r4 <= 0:
                continue

            # ── Intraday 15-min candles on bt_date ────────────────────────
            bt_from = datetime.combine(bt_date, datetime.min.time()).replace(hour=9, minute=15)
            bt_to   = datetime.combine(bt_date, datetime.min.time()).replace(hour=15, minute=30)
            try:
                bt_candles = kite.historical_data(
                    instrument_token,
                    from_date=bt_from,
                    to_date=bt_to,
                    interval="15minute"
                )
            except Exception:
                continue

            if not bt_candles:
                continue

            # ── Find first breakout candle ────────────────────────────────
            breakout_time  = None
            breakout_price = None
            for candle in bt_candles:
                if candle["high"] > r4:
                    # First candle whose HIGH exceeded R4
                    breakout_time  = candle["date"]
                    breakout_price = r4   # the trigger level
                    break

            # ── EOD close of option on bt_date ────────────────────────────
            eod_close = bt_candles[-1]["close"] if bt_candles else None

            # ── % return from R4 trigger to EOD close ─────────────────────
            if breakout_time and eod_close and r4 > 0:
                ret_pct = round(((eod_close - r4) / r4) * 100, 2)
                rows.append({
                    "Symbol":         tradingsymbol,
                    "Open (Stock)":   round(stock_open, 2),
                    "ATM Strike":     atm,
                    "Type":           opt_type,
                    "R4 (Trigger)":   round(r4, 2),
                    "Breakout Time":  ist_time_str(breakout_time),
                    "EOD Close":      round(eod_close, 2),
                    "Return %":       ret_pct,
                    "_ret":           ret_pct,
                    "_type":          opt_type,
                })
            elif not breakout_time and eod_close:
                # No breakout — still log with R4 reference for info
                gap_pct = round(((bt_candles[-1]["high"] - r4) / r4) * 100, 2)
                rows.append({
                    "Symbol":         tradingsymbol,
                    "Open (Stock)":   round(stock_open, 2),
                    "ATM Strike":     atm,
                    "Type":           opt_type,
                    "R4 (Trigger)":   round(r4, 2),
                    "Breakout Time":  "No Breakout",
                    "EOD Close":      round(eod_close, 2),
                    "Return %":       gap_pct,   # gap from R4
                    "_ret":           gap_pct,
                    "_type":          opt_type,
                })

    except Exception:
        pass

    return rows

# ─────────────────────────────────────────────
# FULL BACKTEST SCAN
# ─────────────────────────────────────────────
def run_backtest(kite, bt_date: date) -> dict:
    nfo_df, fno_stocks = fetch_instruments(kite)
    if nfo_df.empty:
        return {"CE": [], "PE": []}

    ce_rows, pe_rows = [], []
    progress = st.progress(0, text="Starting backtest scan…")
    total = len(fno_stocks)

    for idx, symbol in enumerate(fno_stocks):
        rows = backtest_stock(kite, nfo_df, symbol, bt_date)
        for r in rows:
            (ce_rows if r["_type"] == "CE" else pe_rows).append(r)
        progress.progress(
            (idx + 1) / total,
            text=f"Backtesting {symbol}… ({idx+1}/{total})"
        )

    progress.empty()

    # Sort: breakouts first (no "No Breakout"), then by Return% desc
    def sort_key(r):
        no_break = 1 if r["Breakout Time"] == "No Breakout" else 0
        return (no_break, -r["_ret"])

    ce_rows.sort(key=sort_key)
    pe_rows.sort(key=sort_key)
    return {"CE": ce_rows, "PE": pe_rows}

# ─────────────────────────────────────────────
# DISPLAY COLUMNS & CONFIG
# ─────────────────────────────────────────────
DISPLAY_COLS = ["Symbol", "Open (Stock)", "ATM Strike", "R4 (Trigger)",
                "Breakout Time", "EOD Close", "Return %"]

TABLE_CFG = {
    "Symbol":        st.column_config.TextColumn("Symbol",         width="large"),
    "Open (Stock)":  st.column_config.NumberColumn("Stock Open",   format="%.2f"),
    "ATM Strike":    st.column_config.NumberColumn("ATM Strike",   format="%.1f"),
    "R4 (Trigger)":  st.column_config.NumberColumn("R4 (Trigger)", format="%.2f"),
    "Breakout Time": st.column_config.TextColumn("Breakout Time",  width="medium"),
    "EOD Close":     st.column_config.NumberColumn("EOD Close",    format="%.2f"),
    "Return %":      st.column_config.NumberColumn("Return %",     format="%.2f"),
}

def build_df(rows):
    if not rows:
        return pd.DataFrame(columns=DISPLAY_COLS)
    df = pd.DataFrame(rows)[DISPLAY_COLS].copy()
    return df

def render_bt_table(df, opt_type):
    if df.empty:
        st.caption(f"No {opt_type} data for this date.")
        return

    # Colour Return % column: green if positive, red if negative
    def style_ret(val):
        try:
            v = float(val)
            color = "#00e676" if v > 0 else "#ff5252" if v < 0 else "#90a4ae"
            return f"color: {color}; font-weight: 600; font-family: JetBrains Mono, monospace;"
        except Exception:
            return ""

    def style_time(val):
        if val == "No Breakout":
            return "color: #546e7a; font-style: italic;"
        return "color: #ffd740; font-family: JetBrains Mono, monospace;"

    styled = df.style\
        .map(style_ret, subset=["Return %"])\
        .map(style_time, subset=["Breakout Time"])

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        height=min(60 + len(df) * 36, 620),
        column_config=TABLE_CFG,
    )

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in {
    "bt_result": None, "bt_date_run": None,
    "api_key": "", "api_secret": "", "access_token": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="bt-header">
  <div>
    <div class="bt-title">🔬 &nbsp;Backtest — Camarilla R4 Option Scanner</div>
    <div class="bt-subtitle">
      ATM Options &nbsp;·&nbsp; R4 via Prev-Day Last 15-Min Candle
      &nbsp;·&nbsp; First Intraday Breakout &nbsp;·&nbsp; F&amp;O Universe &nbsp;·&nbsp; IST
    </div>
  </div>
  <div>
    <a href="/" target="_self" style="
      font-family:'Rajdhani',sans-serif; font-size:0.8rem; font-weight:600;
      color:#4fc3f7; background:#0a1628; border:1px solid #1e3a5f;
      padding:6px 16px; border-radius:4px; text-decoration:none;
      letter-spacing:1px; text-transform:uppercase;">
      ← Live Scanner
    </a>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CREDENTIALS
# ─────────────────────────────────────────────
api_key, access_token = get_credentials()
_has_creds = bool(api_key and access_token)

if _has_creds:
    _masked = api_key[:6] + "••••••"
    st.markdown(
        f'<div class="cred-saved">✅ &nbsp;Kite Connect credentials loaded &nbsp;|&nbsp; API Key: <code>{_masked}</code></div>',
        unsafe_allow_html=True
    )
    with st.expander("🔄 Change credentials", expanded=False):
        cc1, cc2, cc3 = st.columns(3)
        with cc1: st.session_state.api_key = st.text_input("API Key", value=st.session_state.api_key, type="password")
        with cc2: st.session_state.api_secret = st.text_input("API Secret", value=st.session_state.api_secret, type="password")
        with cc3: st.session_state.access_token = st.text_input("Access Token", value=st.session_state.access_token, type="password")
else:
    st.markdown('<div class="cred-panel">', unsafe_allow_html=True)
    st.markdown('<div class="cred-title">🔑 Zerodha Kite Connect — Enter Credentials</div>', unsafe_allow_html=True)
    cc1, cc2, cc3 = st.columns(3)
    with cc1: st.session_state.api_key = st.text_input("API Key", value=st.session_state.api_key, placeholder="Kite API Key", type="password")
    with cc2: st.session_state.api_secret = st.text_input("API Secret", value=st.session_state.api_secret, placeholder="Kite API Secret", type="password")
    with cc3: st.session_state.access_token = st.text_input("Access Token", value=st.session_state.access_token, placeholder="Today's Access Token", type="password")
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONTROL PANEL — date picker + run button
# ─────────────────────────────────────────────
st.markdown('<div class="ctrl-panel">', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns([1.2, 0.8, 0.8, 3])
with c1:
    # Default to yesterday (last trading session)
    yesterday = date.today() - timedelta(days=1)
    while yesterday.weekday() >= 5:
        yesterday -= timedelta(days=1)
    bt_date = st.date_input(
        "Backtest Date",
        value=yesterday,
        min_value=date(2020, 1, 1),
        max_value=date.today() - timedelta(days=1),
        help="Select any past trading day. Cannot be today (no EOD data yet)."
    )
with c2:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    run_btn = st.button("🔬 Run Backtest", use_container_width=True)
with c3:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    clear_btn = st.button("🗑 Clear", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

if clear_btn:
    st.session_state.bt_result   = None
    st.session_state.bt_date_run = None
    st.rerun()

# ─────────────────────────────────────────────
# RUN BACKTEST
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# KITE CONNECTION TEST
# ─────────────────────────────────────────────
def test_kite_connection(kite) -> tuple:
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

# Show connection error banner immediately if token is bad
if kite is not None:
    _conn_ok, _conn_msg = test_kite_connection(kite)
    if not _conn_ok:
        st.error(_conn_msg)
        st.stop()

if run_btn:
    if not kite:
        st.error("⚠️  Please enter your Kite API Key and Access Token in the credentials panel above.")
    else:
        _ok, _msg = test_kite_connection(kite)
        if not _ok:
            st.error(_msg)
        elif bt_date.weekday() >= 5:
            st.warning("⚠️  Selected date is a weekend. Please choose a trading day (Mon–Fri).")
        else:
            with st.spinner(f"Running backtest for {bt_date.strftime('%d %b %Y')} across {len(get_fno_stocks(kite))} F&O stocks…"):
                result = run_backtest(kite, bt_date)
                st.session_state.bt_result   = result
                st.session_state.bt_date_run = bt_date
            st.rerun()

# ─────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────
if st.session_state.bt_result is None:
    # Show logic explanation
    st.markdown("---")
    st.markdown("""
### How this Backtest works

| Step | Logic |
|------|-------|
| **ATM Strike** | Nearest strike to the stock's **open price on the backtest date** |
| **R4 Calculation** | Camarilla R4 = `Close + (H−L) × 1.1/2` using the **last 15-min candle of the previous trading day** |
| **Breakout Detection** | Scans all 15-min candles from 9:15–3:30 IST on the backtest date; finds the **first candle whose High exceeded R4** |
| **Breakout Time** | IST timestamp of that first breakout candle |
| **EOD Close** | The option's closing price at 3:30 PM IST on the backtest date |
| **Return %** | `(EOD Close − R4) / R4 × 100` — profit if you entered at R4 trigger |

> Rows with **"No Breakout"** mean R4 was never crossed that day — the Return % shows the gap between day's high and R4.
    """)
else:
    res      = st.session_state.bt_result
    run_date = st.session_state.bt_date_run

    ce_break = [r for r in res["CE"] if r["Breakout Time"] != "No Breakout"]
    pe_break = [r for r in res["PE"] if r["Breakout Time"] != "No Breakout"]
    ce_no    = [r for r in res["CE"] if r["Breakout Time"] == "No Breakout"]
    pe_no    = [r for r in res["PE"] if r["Breakout Time"] == "No Breakout"]

    ce_pos = [r for r in ce_break if r["_ret"] > 0]
    pe_pos = [r for r in pe_break if r["_ret"] > 0]
    avg_ce = round(sum(r["_ret"] for r in ce_break) / len(ce_break), 2) if ce_break else 0
    avg_pe = round(sum(r["_ret"] for r in pe_break) / len(pe_break), 2) if pe_break else 0

    # ── Summary cards ──────────────────────────────────────────────────
    st.markdown(f"""
    <div class="sum-row">
      <div class="sum-card">
        <div class="sum-label">Backtest Date</div>
        <div class="sum-value c-purple">{run_date.strftime('%d %b %Y')}</div>
      </div>
      <div class="sum-card">
        <div class="sum-label">CE Breakouts</div>
        <div class="sum-value c-green">{len(ce_break)}</div>
      </div>
      <div class="sum-card">
        <div class="sum-label">PE Breakouts</div>
        <div class="sum-value c-red">{len(pe_break)}</div>
      </div>
      <div class="sum-card">
        <div class="sum-label">CE Win Rate</div>
        <div class="sum-value c-green">{round(len(ce_pos)/len(ce_break)*100) if ce_break else 0}%</div>
      </div>
      <div class="sum-card">
        <div class="sum-label">PE Win Rate</div>
        <div class="sum-value c-red">{round(len(pe_pos)/len(pe_break)*100) if pe_break else 0}%</div>
      </div>
      <div class="sum-card">
        <div class="sum-label">Avg CE Return</div>
        <div class="sum-value {'c-green' if avg_ce >= 0 else 'c-red'}">{avg_ce}%</div>
      </div>
      <div class="sum-card">
        <div class="sum-label">Avg PE Return</div>
        <div class="sum-value {'c-green' if avg_pe >= 0 else 'c-red'}">{avg_pe}%</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Export button ───────────────────────────────────────────────────
    all_rows = res["CE"] + res["PE"]
    if all_rows:
        export_df = pd.DataFrame(all_rows)[DISPLAY_COLS + ["Type"]]
        csv = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Export to CSV",
            data=csv,
            file_name=f"backtest_{run_date.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    st.markdown("---")

    # ── CE / PE tables side by side ─────────────────────────────────────
    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown('<div class="sec-hdr hdr-ce">▲ CE Breakouts (Bullish)</div>', unsafe_allow_html=True)
        render_bt_table(build_df(ce_break), "CE")

        if ce_no:
            with st.expander(f"📋 CE — No Breakout ({len(ce_no)} stocks)", expanded=False):
                render_bt_table(build_df(ce_no), "CE")

    with right_col:
        st.markdown('<div class="sec-hdr hdr-pe">▼ PE Breakouts (Bearish)</div>', unsafe_allow_html=True)
        render_bt_table(build_df(pe_break), "PE")

        if pe_no:
            with st.expander(f"📋 PE — No Breakout ({len(pe_no)} stocks)", expanded=False):
                render_bt_table(build_df(pe_no), "PE")
