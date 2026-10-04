import numpy as np
import pandas as pd

from analytics import calc_horizon_return


def generate_signal(prices):

    prices = pd.Series(
        prices,
        dtype=float,
    ).dropna()

    if len(prices) < 30:

        return {
            "signal":
                "INSUFFICIENT DATA",

            "strength":
                np.nan,

            "bias":
                "NEUTRAL",
        }

    return_1w = (
        calc_horizon_return(
            prices,
            5,
        )
    )

    return_1m = (
        calc_horizon_return(
            prices,
            21,
        )
    )

    ma20 = (
        prices
        .rolling(20)
        .mean()
        .iloc[-1]
    )

    trend = (
        prices.iloc[-1]
        / ma20
        - 1
    )

    score = (

        0.40
        * np.clip(
            return_1w / 5,
            -1,
            1,
        )

        +

        0.45
        * np.clip(
            return_1m / 10,
            -1,
            1,
        )

        +

        0.15
        * np.clip(
            trend / 0.05,
            -1,
            1,
        )
    )

    if score > 0.25:

        signal = (
            "POSITIVE MOMENTUM"
        )

        bias = "OVERWEIGHT"

    elif score < -0.25:

        signal = (
            "NEGATIVE MOMENTUM"
        )

        bias = "UNDERWEIGHT"

    else:

        signal = "MIXED / NEUTRAL"
        bias = "NEUTRAL"

    return {

        "signal":
            signal,

        "strength":
            float(score),

        "bias":
            bias,
    }