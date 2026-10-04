import numpy as np
import pandas as pd

from analytics import returns_frame


# ============================================================
# PORTFOLIO VOLATILITY
# ============================================================

def calc_portfolio_volatility(
    histories,
    weights,
    periods_per_year=252,
):

    symbols = list(
        weights.keys()
    )

    df = returns_frame(
        histories,
        symbols,
    )

    if len(df) < 5:
        return np.nan

    symbols = list(
        df.columns
    )

    # IMPORTANT:
    # Keep actual exposures.
    # Do NOT normalize long/short weights.
    w = np.array(
        [
            float(
                weights.get(
                    symbol,
                    0.0,
                )
            )
            / 100
            for symbol in symbols
        ],
        dtype=float,
    )

    if np.sum(np.abs(w)) == 0:
        return np.nan

    covariance = (
        df.cov().to_numpy()
        * periods_per_year
    )

    variance = float(
        w.T
        @ covariance
        @ w
    )

    return (
        np.sqrt(
            max(
                variance,
                0.0,
            )
        )
        * 100
    )


# ============================================================
# RISK CONTRIBUTION
# ============================================================

def risk_contributions(
    histories,
    weights,
    periods_per_year=252,
):

    symbols = list(
        weights.keys()
    )

    df = returns_frame(
        histories,
        symbols,
    )

    if len(df) < 5:
        return pd.DataFrame()

    symbols = list(
        df.columns
    )

    w = np.array(
        [
            float(
                weights.get(
                    symbol,
                    0.0,
                )
            )
            / 100
            for symbol in symbols
        ],
        dtype=float,
    )

    if np.sum(np.abs(w)) == 0:
        return pd.DataFrame()

    covariance = (
        df.cov().to_numpy()
        * periods_per_year
    )

    portfolio_variance = float(
        w.T
        @ covariance
        @ w
    )

    if portfolio_variance <= 0:
        return pd.DataFrame()

    portfolio_vol = np.sqrt(
        portfolio_variance
    )

    marginal_risk = (
        covariance
        @ w
        / portfolio_vol
    )

    component_risk = (
        w
        * marginal_risk
    )

    risk_pct = (
        component_risk
        / portfolio_vol
        * 100
    )

    return pd.DataFrame({

        "Asset": symbols,

        "Capital Weight": (
            w * 100
        ),

        "Risk Contribution": (
            risk_pct
        ),

    }).set_index("Asset")


# ============================================================
# MINIMUM VARIANCE MODEL
# ============================================================

def min_variance_weights(
    histories,
    symbols,
    periods_per_year=252,
):

    df = returns_frame(
        histories,
        symbols,
    )

    if len(df) < 10:

        return {
            symbol: 0.0
            for symbol in symbols
        }

    covariance = (
        df.cov().to_numpy()
        * periods_per_year
    )

    try:

        inverse_covariance = (
            np.linalg.pinv(
                covariance
            )
        )

        ones = np.ones(
            len(df.columns)
        )

        raw = (
            inverse_covariance
            @ ones
        )

        # Model comparison remains long-only.
        raw = np.clip(
            raw,
            0,
            None,
        )

        if raw.sum() <= 0:

            return {
                symbol: 0.0
                for symbol
                in symbols
            }

        raw = (
            raw
            / raw.sum()
        )

        result = {
            symbol: 0.0
            for symbol in symbols
        }

        for symbol, weight in zip(
            df.columns,
            raw,
        ):

            result[symbol] = (
                float(weight)
                * 100
            )

        return result

    except Exception:

        return {
            symbol: 0.0
            for symbol in symbols
        }


# ============================================================
# LIVE DAILY ATTRIBUTION
# ============================================================

def daily_attribution(
    quotes,
    weights,
):

    rows = []

    gross = sum(
        abs(weight)
        for weight
        in weights.values()
    )

    if gross == 0:
        return pd.DataFrame()

    for symbol, weight in weights.items():

        return_1d = (
            quotes
            .get(symbol, {})
            .get(
                "changePct",
                np.nan,
            )
        )

        portfolio_weight = (
            weight
            / 100
        )

        contribution = (

            portfolio_weight
            * return_1d

            if np.isfinite(
                return_1d
            )

            else np.nan
        )

        rows.append({

            "Asset": symbol,

            "Weight": weight,

            "1D Return": (
                return_1d
            ),

            "Contribution": (
                contribution
            ),
        })

    return (
        pd.DataFrame(rows)
        .set_index("Asset")
    )


# ============================================================
# EXPOSURE SUMMARY
# ============================================================

def exposure_summary(
    weights,
    asset_metadata,
):

    net_exposure = sum(
        weights.values()
    )

    gross_exposure = sum(
        abs(weight)
        for weight
        in weights.values()
    )

    long_exposure = sum(
        weight
        for weight
        in weights.values()
        if weight > 0
    )

    short_exposure = sum(
        abs(weight)
        for weight
        in weights.values()
        if weight < 0
    )

    output = {

        "Net Exposure":
            net_exposure,

        "Gross Exposure":
            gross_exposure,

        "Long Exposure":
            long_exposure,

        "Short Exposure":
            short_exposure,
    }

    asset_types = set()

    for symbol in weights:

        asset_type = (
            asset_metadata
            .get(symbol, {})
            .get(
                "type",
                "OTHER",
            )
        )

        asset_types.add(
            asset_type
        )

    for asset_type in sorted(
        asset_types
    ):

        type_exposure = sum(

            weights.get(
                symbol,
                0.0,
            )

            for symbol in weights

            if (
                asset_metadata
                .get(symbol, {})
                .get(
                    "type",
                    "OTHER",
                )
                == asset_type
            )
        )

        output[
            f"{asset_type} Net"
        ] = type_exposure

    return output