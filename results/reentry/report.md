# Exit at 20%, re-enter after a 15% fall — pre-tax backtest

Actual cached ETF history through 2026-11-16. Same five portfolios, A$20,000 initially and A$1,000 monthly from the following month. The A$10,000 supplemental study is retained in the CSVs. No new price downloads or proxy histories.

## Exact rules

1. Start invested. Exit when net liquidation wealth is at least 20% above the current cycle’s contributed capital. Contributions while invested increase both wealth and the target capital; they are not profit.
2. Sell at the next available open after a closing signal. The re-entry reference is the exact units sold, valued at the exit-day opening market prices before brokerage/slippage. It excludes unrelated cash and unpaid distributions already earned before selling.
3. While waiting, track those same hypothetical units, adjust for splits, and add cash distributions earned after the exit to the reference basket on their ex-dates, without reinvestment. Re-enter when this basket closes at or below 85% of its fixed exit reference. This is a fall from the exit, NOT a fall from a subsequent high. Reference distributions are hypothetical: they are never credited to the real cash account.
4. Re-enter at the following available open even if prices rebound overnight. Invest all affordable cash in whole units at the original target allocations, including contributions and cash interest accumulated while waiting. A$5 brokerage per ETF order and 5bp adverse slippage apply to every purchase and sale.
5. Reset cycle capital to account wealth just before re-entry purchases (cash plus any real distribution receivables). Retained earlier profits are part of this new capital. Future contributions while invested increase it. Repeat the 20% exit/15% re-entry rule; no stop-loss.
6. Continue identical monthly contributions in every strategy. Uninvested cash earns either 0% or a hypothetical constant 3% annually. Actual distributions follow issuer payment dates and reinvest only at scheduled monthly purchases. Final-day signals remain pending; terminal wealth includes estimated liquidation costs.

Example ignoring contributions, distributions and costs: buy at 100, sell at 120.00; re-entry is triggered at 102.00 or below and executes at the next open. The next target becomes 1.20 times the reinvested capital.

**Data qualification:** missing sessions 2024-05-10, 2025-10-24 are omitted without imputation. All crossed windows are flagged; signals, trade timing and drawdowns can be affected. Current common-period results are qualified estimates. No future-performance guarantee.

## Common-period results

2023-05-12–2026-11-16, 0% cash interest. All strategies receive identical contributions. MWR is annualised XIRR; drawdown is adjusted for contributions. Cash days are calendar days fully out of ETF holdings after exits; residual cash while invested is excluded.

| Portfolio | Strategy | Final wealth | Contributed | Profit | MWR/year | Max drawdown | Exits | Re-entries | Cash days | Still waiting |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| NDQ | hold | 96,362 | 62,000 | 34,362 | 19.82% | -21.35% | 0 | 0 | 0 | False |
| NDQ | exit_20_cash | 67,488 | 62,000 | 5,488 | 3.69% | -7.38% | 1 | 0 | 1068 | False |
| NDQ | exit_20_reenter_15 | 67,488 | 62,000 | 5,488 | 3.69% | -7.38% | 1 | 0 | 1068 | True |
| Vanguard diversified | hold | 85,833 | 62,000 | 23,833 | 14.46% | -13.55% | 0 | 0 | 0 | False |
| Vanguard diversified | exit_20_cash | 69,007 | 62,000 | 7,007 | 4.66% | -7.33% | 1 | 0 | 852 | False |
| Vanguard diversified | exit_20_reenter_15 | 69,007 | 62,000 | 7,007 | 4.66% | -7.33% | 1 | 0 | 852 | True |
| Betashares diversified | hold | 86,415 | 62,000 | 24,415 | 14.77% | -13.60% | 0 | 0 | 0 | False |
| Betashares diversified | exit_20_cash | 69,102 | 62,000 | 7,102 | 4.72% | -7.01% | 1 | 0 | 852 | False |
| Betashares diversified | exit_20_reenter_15 | 69,102 | 62,000 | 7,102 | 4.72% | -7.01% | 1 | 0 | 852 | True |
| Betashares growth tilt | hold | 89,261 | 62,000 | 27,261 | 16.26% | -15.80% | 0 | 0 | 0 | False |
| Betashares growth tilt | exit_20_cash | 67,843 | 62,000 | 5,843 | 3.92% | -7.10% | 1 | 0 | 991 | False |
| Betashares growth tilt | exit_20_reenter_15 | 67,843 | 62,000 | 5,843 | 3.92% | -7.10% | 1 | 0 | 991 | True |
| Global growth tilt | hold | 92,108 | 62,000 | 30,108 | 17.71% | -15.97% | 0 | 0 | 0 | False |
| Global growth tilt | exit_20_cash | 68,163 | 62,000 | 6,163 | 4.12% | -7.22% | 1 | 0 | 1011 | False |
| Global growth tilt | exit_20_reenter_15 | 68,163 | 62,000 | 6,163 | 4.12% | -7.22% | 1 | 0 | 1011 | True |

## Interpretation

The re-entry rule completed 0 re-entries across the five common-period accounts. It beat buy-and-hold on terminal wealth in 0 of five comparisons, and beat exiting permanently in 0 of five. 5 accounts were still waiting at the end. These are five selected portfolios on one shared historical path, not independent forecasts.

A market can fall substantially from a later high without ever getting 15% below an earlier sale. That can leave the strategy in cash for years. A successful dip purchase can improve the entry price, but re-entry exposes the account to further losses; there is no downside protection while invested. Repeated trading adds brokerage, slippage and potentially taxable realised gains. The 20% threshold can be crossed and the actual next-open sale still realise less than 20%.

## Twelve- and twenty-four-month entry cohorts

Main study, common-entry dates, 0% cash. Counts are summed across overlapping hypothetical accounts, not a single trading account. Complete and gap-affected windows are separated. Ending without a 15% dip is not a data failure: it is a legitimate cash outcome.

| Portfolio | Horizon | Gap affected | Accounts | Accounts re-entered | Re-entries | Still waiting | Never hit 20% | Median wealth vs hold | Median wealth vs exit/cash |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Betashares diversified | 12m | False | 6 | 0 | 0 | 0 | 6 | 0 | 0 |
| Betashares diversified | 12m | True | 24 | 0 | 0 | 3 | 20 | 0 | 0 |
| Betashares diversified | 24m | True | 18 | 0 | 0 | 16 | 2 | -2,476 | 0 |
| Betashares growth tilt | 12m | False | 6 | 0 | 0 | 0 | 6 | 0 | 0 |
| Betashares growth tilt | 12m | True | 24 | 0 | 0 | 4 | 20 | 0 | 0 |
| Betashares growth tilt | 24m | True | 18 | 0 | 0 | 18 | 0 | -3,861 | 0 |
| Global growth tilt | 12m | False | 6 | 0 | 0 | 1 | 5 | 0 | 0 |
| Global growth tilt | 12m | True | 24 | 1 | 1 | 8 | 14 | 0 | 0 |
| Global growth tilt | 24m | True | 18 | 2 | 2 | 18 | 0 | -5,376 | 0 |
| NDQ | 12m | False | 6 | 2 | 2 | 3 | 3 | 0 | 0 |
| NDQ | 12m | True | 24 | 1 | 1 | 17 | 6 | 0 | 0 |
| NDQ | 24m | True | 18 | 5 | 5 | 18 | 0 | -8,522 | 0 |
| Vanguard diversified | 12m | False | 6 | 0 | 0 | 0 | 6 | 0 | 0 |
| Vanguard diversified | 12m | True | 24 | 0 | 0 | 3 | 21 | 0 | 0 |
| Vanguard diversified | 24m | True | 18 | 0 | 0 | 16 | 2 | -1,513 | 0 |

## Longer histories and cash sensitivity

Each portfolio’s full available history is also tested, but these start dates differ and their terminal wealth must not be compared directly across portfolios. The NDQ and Vanguard histories include COVID and 2022; BGBL portfolios do not. Monthly 3/6/12/24-month and quarterly 36/60-month windows plus annual starts are in `trials.csv`; only complete horizons are included.

| Portfolio | Period | Cash rate | Final wealth | MWR/year | Max drawdown | Exits | Re-entries | Waiting days at end |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| NDQ | common: 2023-05-12–2026-11-16 | 0.00% | 67,488 | 3.69% | -7.38% | 1 | 0 | 1068 |
| NDQ | common: 2023-05-12–2026-11-16 | 3.00% | 71,974 | 6.52% | -7.38% | 1 | 0 | 1068 |
| NDQ | full: 2015-06-02–2026-11-16 | 0.00% | 166,256 | 0.89% | -16.81% | 1 | 0 | 3490 |
| NDQ | full: 2015-06-02–2026-11-16 | 3.00% | 200,923 | 3.76% | -16.81% | 1 | 0 | 3490 |
| Vanguard diversified | common: 2023-05-12–2026-11-16 | 0.00% | 69,007 | 4.66% | -7.33% | 1 | 0 | 852 |
| Vanguard diversified | common: 2023-05-12–2026-11-16 | 3.00% | 72,926 | 7.10% | -7.33% | 1 | 0 | 852 |
| Vanguard diversified | full: 2015-01-02–2026-11-16 | 0.00% | 172,966 | 0.98% | -13.74% | 1 | 0 | 3304 |
| Vanguard diversified | full: 2015-01-02–2026-11-16 | 3.00% | 208,623 | 3.73% | -13.75% | 1 | 0 | 3304 |
| Betashares diversified | common: 2023-05-12–2026-11-16 | 0.00% | 69,102 | 4.72% | -7.01% | 1 | 0 | 852 |
| Betashares diversified | common: 2023-05-12–2026-11-16 | 3.00% | 72,788 | 7.02% | -7.00% | 1 | 0 | 853 |
| Betashares diversified | full: 2023-05-12–2026-11-16 | 0.00% | 69,102 | 4.72% | -7.01% | 1 | 0 | 852 |
| Betashares diversified | full: 2023-05-12–2026-11-16 | 3.00% | 72,788 | 7.02% | -7.00% | 1 | 0 | 853 |
| Betashares growth tilt | common: 2023-05-12–2026-11-16 | 0.00% | 67,843 | 3.92% | -7.10% | 1 | 0 | 991 |
| Betashares growth tilt | common: 2023-05-12–2026-11-16 | 3.00% | 72,133 | 6.62% | -7.10% | 1 | 0 | 991 |
| Betashares growth tilt | full: 2023-05-12–2026-11-16 | 0.00% | 67,843 | 3.92% | -7.10% | 1 | 0 | 991 |
| Betashares growth tilt | full: 2023-05-12–2026-11-16 | 3.00% | 72,133 | 6.62% | -7.10% | 1 | 0 | 991 |
| Global growth tilt | common: 2023-05-12–2026-11-16 | 0.00% | 68,163 | 4.12% | -7.22% | 1 | 0 | 1011 |
| Global growth tilt | common: 2023-05-12–2026-11-16 | 3.00% | 72,542 | 6.87% | -7.22% | 1 | 0 | 1011 |
| Global growth tilt | full: 2023-05-12–2026-11-16 | 0.00% | 68,163 | 4.12% | -7.22% | 1 | 0 | 1011 |
| Global growth tilt | full: 2023-05-12–2026-11-16 | 3.00% | 72,542 | 6.87% | -7.22% | 1 | 0 | 1011 |

## Artifacts, validation and limitations

`trials.csv` contains all account metrics and paired wealth differences. `cycles.csv` and `trade_ledger.csv` retain full/common accounts plus every account that actually re-entered, with trial start/end dates to distinguish overlapping cohorts. `common_daily.csv` records account state, cycle capital, and hypothetical reference basket values. `summary.csv` separates `all_available` cohorts from `common_entries` cohorts; these overlap and must not be pooled. `wealth_*.svg` charts compare all three strategies; identical lines can overlap.

Runtime validation reconciles actual cash, contributions and distribution entitlement for every trial, checks paired contribution equality and verifies all recorded re-entry/exit fills follow their signals. Unit tests include repeated cycles, target resets, accumulated contributions, fixed exit anchors, splits, distributions, pending signals and overnight gaps. Input and output hashes are pinned in `run_manifest.json`.

All results are pre-tax, nominal AUD. Fund fees remain embedded in actual prices; personal CGT, income tax, franking credits and AMIT cost-base adjustments are excluded. Brokerage, slippage, auction liquidity and cash interest are assumptions. XIRR can be extreme over short windows. Sale proceeds are treated as immediately available; re-entry could occur before real settlement, so a broker might require cash or defer the trade. There is no leverage, no borrowing, and no forced sale at the end; liquidation costs are estimated consistently. Historical provider errors and the two missing sessions limit confidence. Funds/allocations were selected retrospectively, and overlapping windows are dependent. This study does not establish an optimal rule or guarantee future returns.
