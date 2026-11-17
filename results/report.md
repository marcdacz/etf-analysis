# ETF accumulation backtest — pre-tax

Actual ETF history through 2026-11-16. Main study: A$20,000 initially, A$1,000 monthly from the following month. Restored from “Retrieve ETF Prices”; the earlier unexecuted script was not available in this workspace. Supplemental study retains the confirmed A$10,000 VAS/VGS comparisons.

**Data qualification:** missing provider prices on 2024-05-10, 2025-10-24. No prices are fabricated or carried forward. These dates are omitted consistently; affected windows have `data_gap_affected=1`. A missed close could change a signal, a sale could be delayed, and maximum drawdown could be understated. Treat affected results as qualified estimates, not fully validated daily-history results. Summary CSV separates complete and affected windows.

## Common-period comparison

All five portfolios start on 2023-05-12, the latest first available ETF price. Cash earns 0%. Final wealth includes estimated liquidation costs; ETF holdings are marked at the final close rather than sold by the strategy. All values AUD. This common window includes data gaps.

| Portfolio | Strategy | Final wealth | Contributed | Profit | MWR/year | Max drawdown | Target days | Exits | Never hit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| NDQ | hold | 96,362 | 62,000 | 34,362 | 19.82% | -21.35% |  | 0 | 0 |
| NDQ | exit_15 | 65,280 | 62,000 | 3,280 | 2.23% | -2.99% | 68 | 1 | 0 |
| NDQ | exit_20 | 67,488 | 62,000 | 5,488 | 3.69% | -7.38% | 215 | 1 | 0 |
| Vanguard diversified | hold | 85,833 | 62,000 | 23,833 | 14.46% | -13.55% |  | 0 | 0 |
| Vanguard diversified | exit_15 | 66,475 | 62,000 | 4,475 | 3.02% | -7.33% | 287 | 1 | 0 |
| Vanguard diversified | exit_20 | 69,007 | 62,000 | 7,007 | 4.66% | -7.33% | 431 | 1 | 0 |
| Betashares diversified | hold | 86,415 | 62,000 | 24,415 | 14.77% | -13.60% |  | 0 | 0 |
| Betashares diversified | exit_15 | 66,222 | 62,000 | 4,222 | 2.86% | -7.01% | 280 | 1 | 0 |
| Betashares diversified | exit_20 | 69,102 | 62,000 | 7,102 | 4.72% | -7.01% | 431 | 1 | 0 |
| Betashares growth tilt | hold | 89,261 | 62,000 | 27,261 | 16.26% | -15.80% |  | 0 | 0 |
| Betashares growth tilt | exit_15 | 66,365 | 62,000 | 4,365 | 2.95% | -7.10% | 255 | 1 | 0 |
| Betashares growth tilt | exit_20 | 67,843 | 62,000 | 5,843 | 3.92% | -7.10% | 292 | 1 | 0 |
| Global growth tilt | hold | 92,108 | 62,000 | 30,108 | 17.71% | -15.97% |  | 0 | 0 |
| Global growth tilt | exit_15 | 66,200 | 62,000 | 4,200 | 2.84% | -7.22% | 250 | 1 | 0 |
| Global growth tilt | exit_20 | 68,163 | 62,000 | 6,163 | 4.12% | -7.22% | 272 | 1 | 0 |

## Reaching 20% within 12 months

Monthly entry cohorts starting after the common inception date. These are historical frequencies, not probabilities of future success. Overlapping windows are dependent; gap status is shown separately.

| Portfolio | Gap affected | Trials | Reached | Completed exits | Never hit | Median days if hit | Median wealth vs hold |
|---|---|---:|---:|---:|---:|---:|---:|
| Betashares diversified | False | 6 | 0 (0.00%) | 0 | 6 |  | 0 |
| Betashares diversified | True | 24 | 4 (16.67%) | 3 | 20 | 346.5 | 0 |
| Betashares growth tilt | False | 6 | 0 (0.00%) | 0 | 6 |  | 0 |
| Betashares growth tilt | True | 24 | 4 (16.67%) | 4 | 20 | 327.0 | 0 |
| Global growth tilt | False | 6 | 1 (16.67%) | 1 | 5 | 357 | 0 |
| Global growth tilt | True | 24 | 10 (41.67%) | 9 | 14 | 311.0 | 0 |
| NDQ | False | 6 | 3 (50.00%) | 3 | 3 | 196 | 0 |
| NDQ | True | 24 | 18 (75.00%) | 18 | 6 | 272.5 | 0 |
| Vanguard diversified | False | 6 | 0 (0.00%) | 0 | 6 |  | 0 |
| Vanguard diversified | True | 24 | 3 (12.50%) | 3 | 21 | 348 | 0 |

## Longer history and market conditions

Full and annual-start trials use each portfolio’s available history. Monthly 3/6/12/24-month windows and quarterly 36/60-month windows end before a calendar-month boundary. Short incomplete windows are excluded rather than counted as failures. Older funds include the COVID decline and 2022 sell-off; BGBL portfolios cannot represent either period. Annual-start trials have unequal lengths and must not be pooled as if comparable.

| Portfolio | History starts | Hold wealth | 15% exit date | 20% exit date |
|---|---|---:|---|---|
| NDQ | 2015-06-02 | 582,781 | 2017-02-22 | 2017-04-27 |
| Vanguard diversified | 2015-01-02 | 375,770 | 2017-04-27 | 2017-10-30 |
| Betashares diversified | 2023-05-12 | 86,415 | 2024-02-19 | 2024-07-17 |
| Betashares growth tilt | 2023-05-12 | 89,261 | 2024-01-23 | 2024-02-29 |
| Global growth tilt | 2023-05-12 | 92,108 | 2024-01-18 | 2024-02-09 |

Selected 12-month entry cohorts show outcomes through different market conditions (0% cash, A$20,000 initially). Funds without actual history are absent.

| Entry year | Portfolio | Strategy | Final wealth | Contributed | Max drawdown | Target days | Never hit |
|---|---|---|---:|---:|---:|---:|---:|
| 2020 | NDQ | hold | 39,303 | 31,000 | -20.81% |  | 0 |
| 2020 | NDQ | exit_15 | 34,437 | 31,000 | -1.57% | 48 | 0 |
| 2020 | NDQ | exit_20 | 36,955 | 31,000 | -20.81% | 190 | 0 |
| 2022 | NDQ | hold | 23,801 | 31,000 | -30.96% |  | 0 |
| 2022 | NDQ | exit_15 | 23,801 | 31,000 | -30.96% |  | 1 |
| 2022 | NDQ | exit_20 | 23,801 | 31,000 | -30.96% |  | 1 |
| 2020 | Vanguard diversified | hold | 32,589 | 31,000 | -26.94% |  | 0 |
| 2020 | Vanguard diversified | exit_15 | 32,589 | 31,000 | -26.94% |  | 1 |
| 2020 | Vanguard diversified | exit_20 | 32,589 | 31,000 | -26.94% |  | 1 |
| 2022 | Vanguard diversified | hold | 28,804 | 31,000 | -18.41% |  | 0 |
| 2022 | Vanguard diversified | exit_15 | 28,804 | 31,000 | -18.41% |  | 1 |
| 2022 | Vanguard diversified | exit_20 | 28,804 | 31,000 | -18.41% |  | 1 |

## Interpretation and trade-offs

In the qualified common-period run, exiting beat buy-and-hold on final wealth in 0 of 10 portfolio/threshold comparisons. This is one market path, not evidence of a universally better rule. The tables and paired `wealth_minus_hold` columns show the cost or benefit of each exit.

Hypothetical cash-yield sensitivity for the common period (all rows cross source-data gaps):

| Portfolio | Strategy | Wealth, cash 0% | Wealth, cash 3% |
|---|---|---:|---:|
| NDQ | exit_15 | 65,280 | 69,928 |
| NDQ | exit_20 | 67,488 | 71,974 |
| Vanguard diversified | exit_15 | 66,475 | 70,659 |
| Vanguard diversified | exit_20 | 69,007 | 72,926 |
| Betashares diversified | exit_15 | 66,222 | 70,405 |
| Betashares diversified | exit_20 | 69,102 | 72,788 |
| Betashares growth tilt | exit_15 | 66,365 | 70,639 |
| Betashares growth tilt | exit_20 | 67,843 | 72,133 |
| Global growth tilt | exit_15 | 66,200 | 70,475 |
| Global growth tilt | exit_20 | 68,163 | 72,542 |

A lower target can secure gains sooner and shorten market exposure, but stops compounding once sold. A higher target can require longer waits and deeper interim losses. Continued contributions dilute percentage gains; they are never investment profit. A 20% portfolio target is not a 20% annual return. Concentrated NDQ exposure can produce a different path from diversified portfolios; adding NDQ overlaps global equity holdings. A200/VAS and BGBL/VGS track different universes and are not exact replicas.

The 3% cash scenarios are hypothetical, constant nominal annual yields applied to all actual cash balances, including idle cash before an exit. They are not historical deposit rates. Compare them with their same-rate buy-and-hold baseline. No re-entry is modelled, so completed exits are at most one per trial. Rolling entry dates represent independent hypothetical accounts, not repeated exit/re-entry cycles.

## Accounting and execution

- Gain = (net liquidation wealth / cumulative external contributions) − 1. Wealth includes cash and earned unpaid distributions; selling costs are estimated for held positions. A$11,500 against A$10,000 is 15%; adding A$1,000 lowers it to 13.64%.
- Month-one capital replaces the first monthly contribution. Subsequent A$1,000 contributions arrive before the first available session each month and continue after selling. No withdrawals.
- Signals use the close; exit fills use the next available open plus adverse slippage. A final-day signal is reported as pending, not a completed exit. Realised gains can fall below target because of overnight moves.
- Whole-unit purchases use fixed cash budgets proportional to allocation deficits, at scheduled opens; brokerage can leave cash idle. No routine selling to rebalance. Distributions reinvest at scheduled purchases only.
- Holders before the ex-date opening receive entitlement. Payment dates release cash; selling between ex-date and payment preserves that receivable. No interest is earned on receivables. No dividend-adjusted prices are used.
- Yahoo quote prices are split-adjusted; the loader reverses future split factors before the engine adjusts units on the split date. The cached actual series have no split events; synthetic fixtures test this path.
- Fund expenses are embedded in observed prices and distributions, so management fees are not deducted again. A$5 per executed ETF order and 5 basis points adverse slippage are explicit assumptions.
- Money-weighted return is annualised XIRR using dated contributions and terminal net wealth. Short-window annualised returns can be extreme. Drawdown uses a contribution-adjusted return index, with contributions at the beginning of a session; it includes costs and avoids contributions hiding losses.

## Data and limitations

Sources and SHA-256 hashes are in `data/raw/manifest.json`; original responses are cached. Normalised records and provider disagreements are in `data/normalized/`. Empty records and zero-volume quotes are excluded, including indicative quotes before first observed trading; these are listed in the audit. Issuer CASH distributions take precedence over Yahoo events, including corrected distribution dates and amounts. Tax credits and gross tax distributions are excluded from spendable cash. Raw records include data outside the chosen test interval; simulations never use future records for signals.

| ETF | First cached price | Last usable price | Issuer distributions | Yahoo disagreements |
|---|---|---|---:|---:|
| VAS | 2011-11-17 | 2026-11-16 | 70 | 2 |
| VGS | 2014-11-21 | 2026-11-16 | 48 | 3 |
| NDQ | 2015-06-02 | 2026-11-16 | 20 | 0 |
| A200 | 2018-05-08 | 2026-11-16 | 34 | 3 |
| BGBL | 2023-05-12 | 2026-11-16 | 7 | 1 |

No proxy or synthetic investment history is included in results. Synthetic values occur only in unit tests. BGBL has a short actual history; five-year BGBL comparisons are unavailable and omitted. There is survivorship/selection bias in choosing today’s funds and allocations, and no optimisation or out-of-sample claim.

Missing/zero-volume provider records, rounded issuer distribution figures, unverified historical opening auction liquidity, settlement delays, spread changes, inflation and historical brokerage schedules limit realism. Cash from a sale is treated as immediately available; there is no re-entry, so settlement does not fund new purchases. Corporate actions and distribution data can be revised by providers; offline cached reruns preserve this snapshot, while `--refresh` intentionally changes it.

Results exclude personal income tax, CGT, franking-credit refunds and AMIT cost-base adjustments. Tax modelling is not implemented; adding it requires explicit parcel-level assumptions and investor circumstances. No historical result guarantees future returns.

## Files and validation

`trials.csv` contains every scenario and metric; `summary.csv` separates common-period rolling cohorts by data quality; `trade_ledger.csv` contains full/common contributions, trades, entitlements and payments; `common_daily.csv` contains common-period wealth paths; `wealth_*.svg` are standalone charts. `run_manifest.json` pins configuration, source files and code hashes. Tests and runtime checks cover accounting and timing; data gaps remain unresolved as disclosed above.
