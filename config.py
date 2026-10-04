BASE_URL = "https://mytxaxpmiysfswfolxem.supabase.co"


# ============================================================
# PREDEFINED ASSET UNIVERSE
# ============================================================

ASSET_UNIVERSE = {

    # ETFs / EQUITY
    "SPY": {
        "name": "S&P 500 ETF",
        "type": "ETF",
    },

    "QQQ": {
        "name": "Nasdaq 100 ETF",
        "type": "ETF",
    },

    "IWM": {
        "name": "Russell 2000 ETF",
        "type": "ETF",
    },

    "EEM": {
        "name": "Emerging Markets ETF",
        "type": "ETF",
    },

    # RATES / CREDIT
    "TLT": {
        "name": "20+ Year Treasury ETF",
        "type": "BOND",
    },

    "HYG": {
        "name": "High Yield Corporate Bond ETF",
        "type": "BOND",
    },

    # COMMODITIES
    "GLD": {
        "name": "Gold ETF",
        "type": "COMMODITY",
    },

    "USO": {
        "name": "Oil ETF",
        "type": "COMMODITY",
    },

    # STOCKS
    "AAPL": {
        "name": "Apple",
        "type": "STOCK",
    },

    "MSFT": {
        "name": "Microsoft",
        "type": "STOCK",
    },

    "NVDA": {
        "name": "Nvidia",
        "type": "STOCK",
    },

    "AMZN": {
        "name": "Amazon",
        "type": "STOCK",
    },

    "META": {
        "name": "Meta",
        "type": "STOCK",
    },

    "GOOGL": {
        "name": "Alphabet",
        "type": "STOCK",
    },

    "TSLA": {
        "name": "Tesla",
        "type": "STOCK",
    },

    "JPM": {
        "name": "JPMorgan",
        "type": "STOCK",
    },

    "GS": {
        "name": "Goldman Sachs",
        "type": "STOCK",
    },

    # CRYPTO
    "BTCUSD": {
        "name": "Bitcoin",
        "type": "CRYPTO",
    },

    "ETHUSD": {
        "name": "Ethereum",
        "type": "CRYPTO",
    },

    "SOLUSD": {
        "name": "Solana",
        "type": "CRYPTO",
    },

    "XRPUSD": {
        "name": "XRP",
        "type": "CRYPTO",
    },

    "ADAUSD": {
        "name": "Cardano",
        "type": "CRYPTO",
    },
}


DEFAULT_ASSETS = [
    "SPY",
    "QQQ",
    "TLT",
    "GLD",
    "BTCUSD",
]


DEFAULT_WEIGHTS = {
    "SPY": 35.0,
    "QQQ": 25.0,
    "TLT": 20.0,
    "GLD": 10.0,
    "BTCUSD": 10.0,
}


# Position limits
MIN_POSITION = -100.0
MAX_POSITION = 100.0