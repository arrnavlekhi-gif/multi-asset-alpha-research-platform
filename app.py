from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


from analytics import (
    calc_drawdowns,
    calc_horizon_return,
    calc_sortino,
    calc_vol,
)

from config import (
    ASSET_UNIVERSE,
    DEFAULT_ASSETS,
    DEFAULT_WEIGHTS,
    MIN_POSITION,
    MAX_POSITION,
)

from data import (
    history_to_series,
    latest_value,
    load_all_data,
)

from health import (
    platform_health,
)

from portfolio import (
    calc_portfolio_volatility,
    daily_attribution,
    exposure_summary,
    min_variance_weights,
    risk_contributions,
)

from regimes import (
    regime_probabilities,
)

from signals import (
    generate_signal,
)


# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(

    page_title=
        "Institutional Alpha Platform",

    page_icon="📈",

    layout="wide",
)


# ============================================================
# FORMATTING
# ============================================================

def fmt_num(
    value,
    decimals=2,
):

    if (
        value is None
        or not np.isfinite(value)
    ):
        return "—"

    return (
        f"{value:.{decimals}f}"
    )


def fmt_pct(
    value,
    decimals=2,
):

    if (
        value is None
        or not np.isfinite(value)
    ):
        return "—"

    return (
        f"{value:+.{decimals}f}%"
    )


def fmt_bps(value):

    if (
        value is None
        or not np.isfinite(value)
    ):
        return "—"

    return (
        f"{value * 100:.0f} bps"
    )


# ============================================================
# SESSION STATE
# ============================================================

if (
    "custom_assets"
    not in st.session_state
):

    st.session_state.custom_assets = {}


if (
    "selected_assets"
    not in st.session_state
):

    st.session_state.selected_assets = (
        DEFAULT_ASSETS.copy()
    )


if (
    "weights"
    not in st.session_state
):

    st.session_state.weights = (
        DEFAULT_WEIGHTS.copy()
    )


if (
    "strategy_name"
    not in st.session_state
):

    st.session_state.strategy_name = (
        "Manual Portfolio"
    )


if (
    "active_sleeve"
    not in st.session_state
):

    st.session_state.active_sleeve = (
        DEFAULT_ASSETS[0]
    )


# ============================================================
# COMBINED UNIVERSE
# ============================================================

asset_metadata = {
    **ASSET_UNIVERSE,
    **st.session_state.custom_assets,
}


# ============================================================
# SIDEBAR — ASSET UNIVERSE BUILDER
# ============================================================

with st.sidebar:

    st.header(
        "Asset Universe"
    )

    st.caption(
        "Select predefined assets or "
        "add your own ticker."
    )


    # --------------------------------------------------------
    # CUSTOM TICKER
    # --------------------------------------------------------

    st.markdown(
        "### Add Custom Asset"
    )

    custom_ticker = (
        st.text_input(
            "Ticker",
            placeholder=
                "e.g. JPM, XOM, BTCUSD",
        )
        .upper()
        .strip()
    )


    custom_name = (
        st.text_input(
            "Asset Name",
            placeholder=
                "e.g. Bitcoin",
        )
        .strip()
    )


    custom_type = (
        st.selectbox(
            "Asset Type",
            [
                "STOCK",
                "ETF",
                "BOND",
                "COMMODITY",
                "CRYPTO",
                "OTHER",
            ],
        )
    )


    if st.button(
        "Add Asset",
        width="stretch",
    ):

        if custom_ticker:

            st.session_state.custom_assets[
                custom_ticker
            ] = {

                "name": (
                    custom_name
                    or custom_ticker
                ),

                "type": custom_type,
            }

            if (
                custom_ticker
                not in
                st.session_state.selected_assets
            ):

                st.session_state.selected_assets.append(
                    custom_ticker
                )

            if (
                custom_ticker
                not in
                st.session_state.weights
            ):

                st.session_state.weights[
                    custom_ticker
                ] = 0.0

            st.rerun()


    # Refresh metadata after custom additions
    asset_metadata = {
        **ASSET_UNIVERSE,
        **st.session_state.custom_assets,
    }


    # --------------------------------------------------------
    # MULTISELECT
    # --------------------------------------------------------

    available_assets = list(
        asset_metadata.keys()
    )


    valid_defaults = [

        symbol

        for symbol
        in st.session_state.selected_assets

        if symbol
        in available_assets
    ]


    selected_assets = (
        st.multiselect(

            "Active Assets",

            options=
                available_assets,

            default=
                valid_defaults,

            format_func=
                lambda symbol:
                    (
                        f"{symbol} — "
                        f"{asset_metadata[symbol]['name']} "
                        f"[{asset_metadata[symbol]['type']}]"
                    ),
        )
    )


    if selected_assets:

        st.session_state.selected_assets = (
            selected_assets
        )


    st.markdown("---")


    st.write(
        f"**Active Assets:** "
        f"{len(st.session_state.selected_assets)}"
    )


# ============================================================
# KEEP WEIGHT DICTIONARY SYNCHRONIZED
# ============================================================

selected_assets = (
    st.session_state.selected_assets
)


if not selected_assets:

    st.warning(
        "Select at least one asset "
        "from the sidebar."
    )

    st.stop()


for symbol in selected_assets:

    if (
        symbol
        not in
        st.session_state.weights
    ):

        st.session_state.weights[
            symbol
        ] = 0.0


st.session_state.weights = {

    symbol:
        st.session_state.weights.get(
            symbol,
            0.0,
        )

    for symbol
    in selected_assets
}


# ============================================================
# HEADER
# ============================================================

title_col, refresh_col = (
    st.columns(
        [6, 1]
    )
)


with title_col:

    st.title(
        "INSTITUTIONAL ALPHA PLATFORM"
    )

    st.caption(
        "LIVE MULTI-ASSET PORTFOLIO "
        "INTELLIGENCE · LONG / SHORT"
    )


with refresh_col:

    if st.button(
        "↻ Refresh",
        width="stretch",
    ):

        st.cache_data.clear()
        st.rerun()


# ============================================================
# DATA LOAD
# ============================================================

try:

    with st.spinner(
        "Synchronizing selected "
        "market and macro data..."
    ):

        quotes, histories, macro = (
            load_all_data(
                tuple(
                    selected_assets
                )
            )
        )

    data_mode = "LIVE"

    last_sync = (
        datetime.now()
        .strftime(
            "%H:%M:%S"
        )
    )


except Exception as error:

    st.error(
        f"Data feed connection "
        f"interrupted: {error}"
    )

    st.stop()


# ============================================================
# MARKET METRICS
# ============================================================

latest_10y = latest_value(
    macro.get(
        "dgs10",
        [],
    ),
    4.25,
)


latest_2y = latest_value(
    macro.get(
        "dgs2",
        [],
    ),
    4.48,
)


latest_oas = latest_value(
    macro.get(
        "hy_oas",
        [],
    ),
    3.42,
)


term_spread = (
    latest_10y
    - latest_2y
)


# SPY is used for macro equity proxies
# only when available.
spy_prices = history_to_series(
    histories.get(
        "SPY",
        [],
    )
)


if not spy_prices.empty:

    spy_vol = calc_vol(
        spy_prices,
    )

    growth_momentum = (
        calc_horizon_return(
            spy_prices,
            21,
        )
    )

else:

    # Fall back to first selected asset.
    proxy_symbol = (
        selected_assets[0]
    )

    proxy_prices = history_to_series(
        histories.get(
            proxy_symbol,
            [],
        )
    )

    spy_vol = calc_vol(
        proxy_prices,
    )

    growth_momentum = (
        calc_horizon_return(
            proxy_prices,
            21,
        )
    )


# ============================================================
# CPI
# ============================================================

cpi = macro.get(
    "cpi",
    [],
)


if len(cpi) >= 13:

    cpi_current = float(
        cpi[-1]["value"]
    )

    cpi_prior = float(
        cpi[-13]["value"]
    )

    inflation_yoy = (

        (
            cpi_current
            - cpi_prior
        )

        / cpi_prior

        * 100

        if cpi_prior != 0

        else np.nan
    )

else:

    inflation_yoy = (
        np.nan
    )


# ============================================================
# PORTFOLIO METRICS
# ============================================================

portfolio_vol = (
    calc_portfolio_volatility(

        histories,

        st.session_state.weights,
    )
)


exposures = (
    exposure_summary(

        st.session_state.weights,

        asset_metadata,
    )
)


# ============================================================
# REGIME
# ============================================================

regime_probs = (
    regime_probabilities(

        inflation_yoy,

        growth_momentum,

        term_spread,

        latest_oas,

        spy_vol,
    )
)


dominant_regime = max(
    regime_probs,
    key=regime_probs.get,
)


# ============================================================
# HEALTH
# ============================================================

health_status, health_detail = (
    platform_health(

        histories,

        macro,

        selected_assets,
    )
)


# ============================================================
# TOP METRICS
# ============================================================

m1, m2, m3, m4, m5 = (
    st.columns(5)
)


m1.metric(
    "Net Exposure",
    fmt_pct(
        exposures[
            "Net Exposure"
        ]
    ),
)


m2.metric(
    "Gross Exposure",
    fmt_pct(
        exposures[
            "Gross Exposure"
        ]
    ),
)


m3.metric(
    "Portfolio Volatility",
    f"{fmt_num(portfolio_vol, 2)}%",
)


m4.metric(
    "10Y - 2Y Spread",
    fmt_bps(
        term_spread
    ),
)


m5.metric(
    "Dominant Regime",
    dominant_regime,
    (
        f"{regime_probs[dominant_regime]:.0f}% "
        f"score probability"
    ),
)


st.info(
    f"Active Strategy: "
    f"{st.session_state.strategy_name}"
)


# ============================================================
# TABS
# ============================================================

(
    tab_market,
    tab_regime,
    tab_portfolio,
    tab_risk,
    tab_signals,
    tab_health,
) = st.tabs(
    [
        "Market Monitor",
        "Regime Monitor",
        "Strategy Deployment",
        "Risk & Attribution",
        "Signal Matrix",
        "Platform Health",
    ]
)


# ============================================================
# MARKET MONITOR
# ============================================================

with tab_market:

    st.subheader(
        "Cross-Asset Momentum Monitor"
    )

    rows = []


    for symbol in selected_assets:

        prices = history_to_series(
            histories.get(
                symbol,
                [],
            )
        )


        live_1d = (
            quotes
            .get(symbol, {})
            .get(
                "changePct",
                np.nan,
            )
        )


        if not np.isfinite(
            live_1d
        ):

            live_1d = (
                calc_horizon_return(
                    prices,
                    1,
                )
            )


        rows.append({

            "Asset":
                symbol,

            "Type":
                asset_metadata
                .get(symbol, {})
                .get(
                    "type",
                    "OTHER",
                ),

            "1D":
                live_1d,

            "1W":
                calc_horizon_return(
                    prices,
                    5,
                ),

            "1M":
                calc_horizon_return(
                    prices,
                    21,
                ),

            "3M":
                calc_horizon_return(
                    prices,
                    63,
                ),
        })


    momentum_df = (
        pd.DataFrame(rows)
        .set_index("Asset")
    )


    st.dataframe(

        momentum_df.style.format({

            "1D": "{:+.2f}%",

            "1W": "{:+.2f}%",

            "1M": "{:+.2f}%",

            "3M": "{:+.2f}%",
        }),

        width="stretch",
    )


# ============================================================
# REGIME MONITOR
# ============================================================

with tab_regime:

    st.subheader(
        "Live Macro Regime Monitor"
    )


    regime_df = (
        pd.DataFrame({

            "Regime":
                list(
                    regime_probs.keys()
                ),

            "Probability":
                list(
                    regime_probs.values()
                ),
        })

        .sort_values(
            "Probability",
            ascending=False,
        )
    )


    fig = go.Figure(

        go.Bar(

            x=
                regime_df[
                    "Probability"
                ],

            y=
                regime_df[
                    "Regime"
                ],

            orientation="h",

            text=
                regime_df[
                    "Probability"
                ].map(
                    lambda x:
                        f"{x:.1f}%"
                ),

            textposition="auto",
        )
    )


    fig.update_layout(

        height=350,

        xaxis_title=
            "Probability (%)",

        yaxis_title="",
    )


    st.plotly_chart(
        fig,
        width="stretch",
    )


    c1, c2, c3, c4 = (
        st.columns(4)
    )


    c1.metric(
        "CPI YoY",
        fmt_pct(
            inflation_yoy
        ),
    )


    c2.metric(
        "Growth Momentum",
        fmt_pct(
            growth_momentum
        ),
    )


    c3.metric(
        "Yield Curve",
        fmt_bps(
            term_spread
        ),
    )


    c4.metric(
        "HY OAS",
        fmt_pct(
            latest_oas
        ),
    )


# ============================================================
# STRATEGY DEPLOYMENT
# ============================================================

with tab_portfolio:

    st.subheader(
        "Strategy Deployment"
    )


    st.caption(
        "Enter the target weights "
        "produced by your backtester. "
        "Positive weights are long. "
        "Negative weights are short."
    )


    strategy_name = (
        st.text_input(

            "Strategy Name",

            value=
                st.session_state.strategy_name,
        )
    )


    strategy_weights = {}


    for symbol in selected_assets:

        metadata = (
            asset_metadata.get(
                symbol,
                {},
            )
        )


        strategy_weights[
            symbol
        ] = st.number_input(

            (
                f"{symbol} — "
                f"{metadata.get('name', symbol)} "
                f"Target Weight (%)"
            ),

            min_value=
                float(
                    MIN_POSITION
                ),

            max_value=
                float(
                    MAX_POSITION
                ),

            value=
                float(
                    st.session_state.weights.get(
                        symbol,
                        0.0,
                    )
                ),

            step=1.0,

            key=
                f"strategy_weight_{symbol}",
        )


    if st.button(
        "Apply Strategy",
        width="stretch",
    ):

        st.session_state.weights = (
            strategy_weights.copy()
        )

        st.session_state.strategy_name = (
            strategy_name
        )

        st.rerun()


    st.divider()


    # --------------------------------------------------------
    # EXPOSURE SUMMARY
    # --------------------------------------------------------

    live_exposure = (
        exposure_summary(

            st.session_state.weights,

            asset_metadata,
        )
    )


    e1, e2, e3, e4 = (
        st.columns(4)
    )


    e1.metric(
        "Net Exposure",
        fmt_pct(
            live_exposure[
                "Net Exposure"
            ]
        ),
    )


    e2.metric(
        "Gross Exposure",
        fmt_pct(
            live_exposure[
                "Gross Exposure"
            ]
        ),
    )


    e3.metric(
        "Long Exposure",
        fmt_pct(
            live_exposure[
                "Long Exposure"
            ]
        ),
    )


    e4.metric(
        "Short Exposure",
        fmt_pct(
            live_exposure[
                "Short Exposure"
            ]
        ),
    )


    # --------------------------------------------------------
    # CURRENT STRATEGY TABLE
    # --------------------------------------------------------

    strategy_table = (
        pd.DataFrame({

            "Weight":
                pd.Series(
                    st.session_state.weights
                ),
        })
    )


    strategy_table[
        "Position"
    ] = (
        strategy_table[
            "Weight"
        ]
        .apply(
            lambda weight:

                "LONG"
                if weight > 0

                else "SHORT"
                if weight < 0

                else "FLAT"
        )
    )


    strategy_table[
        "Type"
    ] = [

        asset_metadata
        .get(symbol, {})
        .get(
            "type",
            "OTHER",
        )

        for symbol
        in strategy_table.index
    ]


    st.dataframe(

        strategy_table.style.format({
            "Weight": "{:+.1f}%"
        }),

        width="stretch",
    )


    # --------------------------------------------------------
    # MODEL COMPARISON
    # --------------------------------------------------------

    st.markdown(
        "### Long-Only Minimum Variance Comparison"
    )


    model_weights = (
        min_variance_weights(

            histories,

            selected_assets,
        )
    )


    comparison = (
        pd.DataFrame({

            "Strategy":
                pd.Series(
                    st.session_state.weights
                ),

            "Min Variance":
                pd.Series(
                    model_weights
                ),
        })

        .fillna(0)
    )


    st.dataframe(

        comparison.style.format(
            "{:+.1f}%"
        ),

        width="stretch",
    )


    strategy_vol = (
        calc_portfolio_volatility(

            histories,

            st.session_state.weights,
        )
    )


    model_vol = (
        calc_portfolio_volatility(

            histories,

            model_weights,
        )
    )


    c1, c2 = (
        st.columns(2)
    )


    c1.metric(
        "Strategy Volatility",
        f"{fmt_num(strategy_vol)}%",
    )


    c2.metric(
        "Min-Variance Volatility",
        f"{fmt_num(model_vol)}%",
    )


    # --------------------------------------------------------
    # ASSET CLASS EXPOSURES
    # --------------------------------------------------------

    st.markdown(
        "### Exposure Map"
    )


    exposure_rows = [

        {
            "Exposure":
                key,

            "Value":
                value,
        }

        for key, value
        in live_exposure.items()
    ]


    st.dataframe(

        pd.DataFrame(
            exposure_rows
        ).style.format({
            "Value": "{:+.1f}%"
        }),

        width="stretch",

        hide_index=True,
    )


# ============================================================
# RISK + ATTRIBUTION
# ============================================================

with tab_risk:

    left, right = (
        st.columns(2)
    )


    with left:

        st.subheader(
            "Risk Contribution"
        )


        risk_df = (
            risk_contributions(

                histories,

                st.session_state.weights,
            )
        )


        if not risk_df.empty:

            st.dataframe(

                risk_df.style.format({

                    "Capital Weight":
                        "{:+.1f}%",

                    "Risk Contribution":
                        "{:+.1f}%",
                }),

                width="stretch",
            )


            risk_chart = (
                go.Figure(

                    go.Bar(

                        x=
                            risk_df.index,

                        y=
                            risk_df[
                                "Risk Contribution"
                            ],

                        text=
                            risk_df[
                                "Risk Contribution"
                            ].map(
                                lambda x:
                                    f"{x:+.1f}%"
                            ),

                        textposition=
                            "auto",
                    )
                )
            )


            risk_chart.update_layout(

                height=320,

                yaxis_title=
                    "Risk Contribution (%)",
            )


            st.plotly_chart(
                risk_chart,
                width="stretch",
            )


    with right:

        st.subheader(
            "Live Return Attribution"
        )


        attribution = (
            daily_attribution(

                quotes,

                st.session_state.weights,
            )
        )


        if not attribution.empty:

            st.dataframe(

                attribution.style.format({

                    "Weight":
                        "{:+.1f}%",

                    "1D Return":
                        "{:+.2f}%",

                    "Contribution":
                        "{:+.2f}%",
                }),

                width="stretch",
            )


            portfolio_1d = (
                attribution[
                    "Contribution"
                ]
                .dropna()
                .sum()
            )


            st.metric(
                "Estimated Portfolio 1D Return",
                fmt_pct(
                    portfolio_1d,
                    2,
                ),
            )


    st.divider()


    # --------------------------------------------------------
    # DRAWDOWN
    # --------------------------------------------------------

    st.subheader(
        "Asset Drawdown Monitor"
    )


    valid_drawdown_assets = [

        symbol

        for symbol
        in selected_assets

        if len(
            histories.get(
                symbol,
                [],
            )
        ) > 1
    ]


    if valid_drawdown_assets:

        if (
            st.session_state.active_sleeve
            not in
            valid_drawdown_assets
        ):

            st.session_state.active_sleeve = (
                valid_drawdown_assets[0]
            )


        selected_sleeve = (
            st.selectbox(

                "Select Asset",

                valid_drawdown_assets,

                index=
                    valid_drawdown_assets.index(
                        st.session_state.active_sleeve
                    ),
            )
        )


        st.session_state.active_sleeve = (
            selected_sleeve
        )


        selected_prices = (
            history_to_series(

                histories.get(
                    selected_sleeve,
                    [],
                )
            )
        )


        drawdown = (
            calc_drawdowns(
                selected_prices
            )
        )


        if not drawdown.empty:

            dd_fig = (
                go.Figure()
            )


            dd_fig.add_trace(

                go.Scatter(

                    x=
                        drawdown.index,

                    y=
                        drawdown.values,

                    mode=
                        "lines",

                    fill=
                        "tozeroy",

                    name=
                        selected_sleeve,
                )
            )


            dd_fig.update_layout(

                height=350,

                title=
                    (
                        f"{selected_sleeve} "
                        f"Underwater Drawdown"
                    ),

                yaxis_title=
                    "Drawdown (%)",
            )


            st.plotly_chart(
                dd_fig,
                width="stretch",
            )


            st.metric(
                "Maximum Drawdown",
                fmt_pct(
                    drawdown.min()
                ),
            )


# ============================================================
# SIGNAL MATRIX
# ============================================================

with tab_signals:

    st.subheader(
        "Live Signal Matrix"
    )


    st.caption(
        "Signal Strength is a model "
        "score based on 1W momentum, "
        "1M momentum and 20-day trend. "
        "It is not a probability."
    )


    signal_rows = []


    for symbol in selected_assets:

        prices = (
            history_to_series(

                histories.get(
                    symbol,
                    [],
                )
            )
        )


        result = (
            generate_signal(
                prices
            )
        )


        asset_type = (
            asset_metadata
            .get(symbol, {})
            .get(
                "type",
                "OTHER",
            )
        )


        periods_per_year = (

            365

            if asset_type
            == "CRYPTO"

            else 252
        )


        signal_rows.append({

            "Asset":
                symbol,

            "Type":
                asset_type,

            "Signal":
                result[
                    "signal"
                ],

            "Bias":
                result[
                    "bias"
                ],

            "Strength":
                result[
                    "strength"
                ],

            "1W":
                calc_horizon_return(
                    prices,
                    5,
                ),

            "1M":
                calc_horizon_return(
                    prices,
                    21,
                ),

            "Volatility":
                calc_vol(
                    prices,
                    periods_per_year,
                ),

            "Sortino":
                calc_sortino(
                    prices,
                    periods_per_year=
                        periods_per_year,
                ),
        })


    signal_df = (
        pd.DataFrame(
            signal_rows
        )
        .set_index(
            "Asset"
        )
    )


    st.dataframe(

        signal_df.style.format({

            "Strength":
                "{:+.2f}",

            "1W":
                "{:+.2f}%",

            "1M":
                "{:+.2f}%",

            "Volatility":
                "{:.2f}%",

            "Sortino":
                "{:.2f}",
        }),

        width="stretch",
    )


# ============================================================
# PLATFORM HEALTH
# ============================================================

with tab_health:

    st.subheader(
        "Platform Health"
    )


    st.metric(
        "System Status",
        health_status,
    )


    st.write(
        health_detail
    )


    health_rows = []


    for symbol in selected_assets:

        observations = len(
            histories.get(
                symbol,
                [],
            )
        )


        health_rows.append({

            "Source":
                symbol,

            "Type":
                asset_metadata
                .get(symbol, {})
                .get(
                    "type",
                    "OTHER",
                ),

            "Observations":
                observations,

            "Status":
                (
                    "OK"
                    if observations >= 30
                    else "LIMITED"
                ),
        })


    for key in [
        "cpi",
        "dgs10",
        "dgs2",
        "hy_oas",
        "fed_funds",
    ]:

        observations = len(
            macro.get(
                key,
                [],
            )
        )


        health_rows.append({

            "Source":
                key,

            "Type":
                "MACRO",

            "Observations":
                observations,

            "Status":
                (
                    "OK"
                    if observations > 0
                    else "MISSING"
                ),
        })


    st.dataframe(

        pd.DataFrame(
            health_rows
        ),

        width="stretch",

        hide_index=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()


st.caption(

    f"INSTITUTIONAL ALPHA PLATFORM · "
    f"{data_mode} · "
    f"LAST SYNC {last_sync} · "
    f"NO INVESTMENT ADVICE"
)