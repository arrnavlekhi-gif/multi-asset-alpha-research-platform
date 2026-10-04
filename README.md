# Multi-Asset Alpha Research Platform

An interactive Python/Streamlit dashboard for monitoring cross-asset signals, macro regimes, portfolio exposures and risk in a single research interface.

The project is designed as a **portfolio-intelligence and signal-monitoring tool**, rather than a claim of a standalone profitable trading strategy.

## What the platform does

The dashboard combines market and macro data with systematic analytics across a configurable multi-asset universe. The default universe spans:

- U.S. equity ETFs and individual equities
- Treasury and high-yield bond ETFs
- gold and oil ETFs
- major cryptocurrencies

Users can also add custom assets supported by the underlying data service.

## Research components

### Cross-asset signal engine

Each asset receives a simple systematic momentum score built from:

- 1-week return;
- 1-month return;
- distance from the 20-day moving average.

The components are combined into a bounded score and mapped to positive-momentum, negative-momentum or neutral classifications, together with an overweight/underweight/neutral bias.

The signal is intentionally transparent and heuristic: it is a monitoring indicator, not a fitted forecasting model.

### Macro regime model

The platform maps five macro/market inputs into four regime probabilities:

- inflation;
- growth momentum;
- term spread;
- high-yield credit spread;
- equity volatility.

The resulting regimes are:

- Expansion
- Inflationary Growth
- Slowdown
- Risk-Off / Crisis

The model uses explicit rule-based scores transformed into probabilities with a softmax calculation. These probabilities should therefore be interpreted as a research classification framework rather than statistically estimated economic probabilities.

### Portfolio analytics

The platform supports manual portfolio weights and a long-only minimum-variance model. Portfolio analytics include:

- covariance-based annualized volatility;
- asset-level risk contribution;
- live daily return attribution;
- capital weights;
- gross, net, long and short exposure summaries.

Long/short manual portfolios retain their actual signed exposures rather than automatically normalizing them away.

### Risk and monitoring

The dashboard also provides:

- annualized asset volatility;
- Sortino ratio;
- drawdown series;
- horizon returns;
- covariance/correlation inputs;
- live portfolio attribution;
- data-feed and platform-health checks.

## Project structure

```text
multi-asset-alpha-research-platform/
├── README.md
├── .gitignore
├── app.py
├── analytics.py
├── config.py
├── data.py
├── health.py
├── portfolio.py
├── regimes.py
├── signals.py
└── requirements.txt
```

## Running locally

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the dashboard:

```bash
streamlit run app.py
```

Streamlit will normally expose the application at:

```text
http://localhost:8501
```

## Data architecture

The application retrieves market and economic data through an existing Supabase-hosted proxy endpoint configured in `config.py`.

The repository contains **no API keys, passwords or authentication tokens**. If the proxy endpoint is moved or retired, update `BASE_URL` in `config.py` and ensure the replacement service exposes the endpoints expected by `data.py`.

## Methodological notes

### Portfolio volatility

Portfolio variance is computed from the historical return covariance matrix:

```text
σ²_p = w'Σw
```

and annualized using the configured periods-per-year assumption.

### Risk contribution

Marginal and component risk are derived from the same covariance matrix, allowing the dashboard to distinguish capital allocation from each asset's contribution to total portfolio volatility.

### Minimum-variance allocation

The model uses the pseudo-inverse of the covariance matrix and clips negative raw weights, producing a normalized long-only minimum-variance comparison portfolio.

## Limitations

This project is a research dashboard, not a production execution system.

Important limitations include:

- the momentum score uses fixed heuristic weights rather than parameters estimated from a predictive model;
- regime probabilities are rule-based classifications, not probabilities estimated from a formal econometric regime-switching model;
- historical covariance estimates are sensitive to the selected sample and asset universe;
- minimum-variance weights can be unstable when covariance estimates change;
- the dashboard depends on the availability and quality of its external data proxy;
- live quotes and historical data do not model execution, slippage, liquidity or market impact;
- displayed analytics should not be interpreted as evidence of persistent alpha without a separate out-of-sample backtest.

## Technology

Python, Streamlit, pandas, NumPy, Plotly, Requests and Matplotlib.

## Purpose

The repository demonstrates how market data, macro indicators, systematic signals, portfolio construction, risk attribution and interactive visualization can be combined into a compact cross-asset research application.

For research and educational purposes only. Not investment advice.
