import numpy as np
import pandas as pd
import requests
import streamlit as st

from config import BASE_URL


# ============================================================
# DATA PARSING
# ============================================================

def parse_econ_series(payload):

    if isinstance(payload, list):
        rows = payload

    elif isinstance(payload, dict):
        rows = (
            payload.get("points")
            or payload.get("data")
            or []
        )

    else:
        rows = []

    output = []

    for row in rows:

        if not isinstance(row, dict):
            continue

        date = str(
            row.get("date")
            or row.get("period_start")
            or row.get("period_date")
            or ""
        )[:10]

        raw_value = (
            row.get("value")
            if row.get("value") is not None

            else row.get("val")
            if row.get("val") is not None

            else row.get("index_value")
            if row.get("index_value") is not None

            else row.get("level")
        )

        try:
            value = float(raw_value)

        except (TypeError, ValueError):
            continue

        if date and np.isfinite(value):

            output.append({
                "date": date,
                "value": value,
            })

    return sorted(
        output,
        key=lambda x: x["date"],
    )


def history_to_series(history):

    if not history:
        return pd.Series(dtype=float)

    df = pd.DataFrame(history)

    if df.empty or "close" not in df.columns:
        return pd.Series(dtype=float)

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    df["close"] = pd.to_numeric(
        df["close"],
        errors="coerce",
    )

    df = (
        df
        .dropna(subset=["date", "close"])
        .query("close > 0")
        .sort_values("date")
        .set_index("date")
    )

    return df["close"]


def latest_value(series, fallback=np.nan):

    if series:

        try:
            return float(
                series[-1]["value"]
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            pass

    return fallback


# ============================================================
# MARKET API
# ============================================================

@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def fetch_batch_quotes(symbols):

    symbols = tuple(symbols)

    if not symbols:
        return {}

    response = requests.post(

        f"{BASE_URL}/functions/v1/fmp-api-proxy",

        json={
            "endpoint": "batch-quote",

            "params": {
                "symbols": ",".join(symbols)
            },
        },

        headers={
            "Content-Type": "application/json"
        },

        timeout=20,
    )

    response.raise_for_status()

    payload = response.json()

    raw_quotes = (

        payload.get("data", [])

        if isinstance(payload, dict)

        else payload
    )

    quotes = {}

    if isinstance(raw_quotes, list):

        for quote in raw_quotes:

            symbol = quote.get("symbol")

            if not symbol:
                continue

            try:
                pe = (
                    float(quote.get("pe"))
                    if quote.get("pe") is not None
                    else np.nan
                )

            except (TypeError, ValueError):
                pe = np.nan

            quotes[symbol] = {

                "symbol": symbol,

                "price": float(
                    quote.get("price") or 0
                ),

                "changePct": float(
                    quote.get(
                        "changesPercentage"
                    )
                    or 0
                ),

                "pe": pe,

                "marketCap": float(
                    quote.get("marketCap")
                    or 0
                ),
            }

    return quotes


@st.cache_data(
    ttl=900,
    show_spinner=False,
)
def fetch_history(symbol):

    response = requests.post(

        f"{BASE_URL}/functions/v1/fmp-api-proxy",

        json={
            "endpoint": "historical-price-full",

            "params": {
                "symbol": symbol
            },
        },

        headers={
            "Content-Type": "application/json"
        },

        timeout=20,
    )

    response.raise_for_status()

    payload = response.json()

    if isinstance(payload, dict):

        raw = (
            payload.get("data")
            or payload.get("historical")
            or []
        )

    elif isinstance(payload, list):

        raw = payload

    else:

        raw = []

    history = []

    # More observations than before so
    # 3M / momentum / covariance metrics
    # have enough data.
    for row in raw[:365]:

        if not isinstance(row, dict):
            continue

        try:
            close = float(
                row.get("close")
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

        if close > 0:

            history.append({

                "date": row.get(
                    "date",
                    "",
                ),

                "close": close,
            })

    return sorted(
        history,
        key=lambda x: x["date"],
    )


# ============================================================
# ECONOMIC DATA
# ============================================================

@st.cache_data(
    ttl=900,
    show_spinner=False,
)
def fetch_econ(
    alias,
    limit=90,
):

    response = requests.post(

        f"{BASE_URL}/functions/v1/econ-fetch",

        json={
            "alias": alias,
            "limit": limit,
            "live_only": True,
        },

        headers={
            "Content-Type": "application/json"
        },

        timeout=20,
    )

    response.raise_for_status()

    return parse_econ_series(
        response.json()
    )


# ============================================================
# COMPLETE DATA PIPELINE
# ============================================================

def load_all_data(symbols):

    symbols = tuple(
        dict.fromkeys(symbols)
    )

    quotes = {}

    if symbols:

        try:
            quotes = fetch_batch_quotes(
                symbols
            )

        except Exception:
            quotes = {}

    histories = {}

    for symbol in symbols:

        try:

            histories[symbol] = (
                fetch_history(symbol)
            )

        except Exception:

            histories[symbol] = []

    macro_specs = {

        "cpi": 24,

        "dgs10": 90,

        "dgs2": 90,

        "hy_oas": 90,

        "fed_funds": 90,
    }

    macro = {}

    for alias, limit in macro_specs.items():

        try:

            macro[alias] = fetch_econ(
                alias,
                limit,
            )

        except Exception:

            macro[alias] = []

    return (
        quotes,
        histories,
        macro,
    )