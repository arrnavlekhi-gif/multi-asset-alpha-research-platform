import numpy as np


def regime_probabilities(
    inflation_yoy,
    growth_momentum,
    term_spread,
    hy_oas,
    equity_vol,
):

    infl = (
        inflation_yoy
        if np.isfinite(
            inflation_yoy
        )
        else 3.0
    )

    growth = (
        growth_momentum
        if np.isfinite(
            growth_momentum
        )
        else 0.0
    )

    curve = (
        term_spread
        if np.isfinite(
            term_spread
        )
        else 0.0
    )

    oas = (
        hy_oas
        if np.isfinite(
            hy_oas
        )
        else 3.5
    )

    vol = (
        equity_vol
        if np.isfinite(
            equity_vol
        )
        else 18.0
    )

    expansion = (

        1.1

        + 0.35
        * np.clip(
            growth / 3,
            -2,
            2,
        )

        + 0.25
        * np.clip(
            curve / 1,
            -2,
            2,
        )

        - 0.20
        * np.clip(
            (oas - 3.5)
            / 1.5,
            -2,
            2,
        )

        - 0.20
        * np.clip(
            (vol - 18)
            / 8,
            -2,
            2,
        )
    )

    inflationary = (

        0.7

        + 0.30
        * np.clip(
            (infl - 2.5)
            / 1.5,
            -2,
            2,
        )

        + 0.15
        * np.clip(
            growth / 3,
            -2,
            2,
        )

        + 0.10
        * np.clip(
            curve / 1,
            -2,
            2,
        )
    )

    slowdown = (

        0.7

        - 0.30
        * np.clip(
            growth / 3,
            -2,
            2,
        )

        - 0.25
        * np.clip(
            curve / 1,
            -2,
            2,
        )

        + 0.15
        * np.clip(
            (oas - 3.5)
            / 1.5,
            -2,
            2,
        )
    )

    risk_off = (

        0.5

        + 0.35
        * np.clip(
            (oas - 3.5)
            / 1.5,
            -2,
            2,
        )

        + 0.35
        * np.clip(
            (vol - 18)
            / 8,
            -2,
            2,
        )

        - 0.20
        * np.clip(
            growth / 3,
            -2,
            2,
        )
    )

    scores = np.array(
        [
            expansion,
            inflationary,
            slowdown,
            risk_off,
        ],
        dtype=float,
    )

    exponential_scores = np.exp(
        scores
        - scores.max()
    )

    probabilities = (
        exponential_scores
        / exponential_scores.sum()
    )

    labels = [

        "Expansion",

        "Inflationary Growth",

        "Slowdown",

        "Risk-Off / Crisis",
    ]

    return dict(
        zip(
            labels,
            probabilities * 100,
        )
    )