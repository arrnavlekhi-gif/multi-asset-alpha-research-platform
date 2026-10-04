def platform_health(
    histories,
    macro,
    selected_assets,
):

    issues = []

    for symbol in selected_assets:

        observations = len(
            histories.get(
                symbol,
                [],
            )
        )

        if observations < 30:

            issues.append(
                f"{symbol}: limited history"
            )

    required_macro = [
        "cpi",
        "dgs10",
        "dgs2",
        "hy_oas",
    ]

    for key in required_macro:

        if not macro.get(key):

            issues.append(
                f"{key}: unavailable"
            )

    if not issues:

        return (
            "HEALTHY",
            "All selected market and core macro feeds are available.",
        )

    if len(issues) <= 2:

        return (
            "DEGRADED",
            " · ".join(issues),
        )

    return (
        "ATTENTION",
        " · ".join(issues),
    )