import numpy as np
import pandas as pd

from data import history_to_series


# ============================================================
# VOLATILITY
# ============================================================

def calc_vol(
    prices,
    periods_per_year=252,
):

    prices = pd.Series(
        prices,
        dtype=float,
    ).dropna()

    if len(prices) < 5:
        return np.nan

    log_returns = np.log(
        prices / prices.shift(1)
    ).dropna()

    if len(log_returns) < 2:
        return np.nan

    return (
        log_returns.std(ddof=1)
        * np.sqrt(periods_per_year)
        * 100
    )


# ============================================================
# SORTINO
# ============================================================

def calc_sortino(
    prices,
    annual_rf=0.04,
    periods_per_year=252,
):

    prices = pd.Series(
        prices,
        dtype=float,
    ).dropna()

    if len(prices) < 10:
        return np.nan

    returns = (
        prices
        .pct_change()
        .dropna()
    )

    if returns.empty:
        return np.nan

    daily_rf = (
        (1 + annual_rf)
        ** (1 / periods_per_year)
        - 1
    )

    excess = (
        returns
        - daily_rf
    )

    downside = np.minimum(
        excess,
        0.0,
    )

    downside_dev = np.sqrt(
        np.mean(
            np.square(downside)
        )
    )

    if downside_dev == 0:
        return np.nan

    annual_excess = (
        excess.mean()
        * periods_per_year
    )

    annual_downside = (
        downside_dev
        * np.sqrt(
            periods_per_year
        )
    )

    return (
        annual_excess
        / annual_downside
    )


# ============================================================
# DRAWDOWN
# ============================================================

def calc_drawdowns(prices):

    prices = pd.Series(
        prices,
        dtype=float,
    ).dropna()

    if prices.empty:
        return pd.Series(
            dtype=float
        )

    peak = prices.cummax()

    return (
        (prices / peak)
        - 1
    ) * 100


# ============================================================
# HORIZON RETURNS
# ============================================================

def calc_horizon_return(
    prices,
    trading_days,
):

    prices = pd.Series(
        prices,
        dtype=float,
    ).dropna()

    if len(prices) <= trading_days:
        return np.nan

    return (
        (
            prices.iloc[-1]
            / prices.iloc[
                -1 - trading_days
            ]
        )
        - 1
    ) * 100


# ============================================================
# RETURN MATRIX
# ============================================================

def returns_frame(
    histories,
    symbols,
):

    data = {}

    for symbol in symbols:

        prices = history_to_series(
            histories.get(
                symbol,
                [],
            )
        )

        if len(prices) >= 5:

            data[symbol] = (
                prices
                .pct_change()
            )

    if not data:

        return pd.DataFrame()

    # Intersection of available dates.
    # For mixed crypto/equity portfolios this
    # naturally leaves common trading dates.
    return (
        pd.DataFrame(data)
        .dropna(how="any")
    )