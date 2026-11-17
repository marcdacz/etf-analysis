# Peak-based re-entry and monthly trend allocation — pre-tax

Actual ETF data through 2026-11-16. Main accounts start with A$20,000 and receive A$1,000 monthly from the following month. Same five main portfolios and A$10,000 supplemental accounts as previous studies. Results are in nominal AUD. No ETF history is extended before inception.

**Data qualification:** missing sessions 2024-05-10, 2025-10-24 are omitted without inventing prices. Affected windows are flagged; missed signals, delayed fills and understated drawdowns remain possible. These are qualified historical results, not forecasts.

## Exact strategies

- **Buy-and-hold:** remains invested and buys monthly.
- **Exit/cash and fixed re-entry:** prior controls. Exit at 20% cycle gain; either stay in cash permanently or re-enter after a 15% decline from the exit basket value.
- **Peak re-entry:** retain the same 20% exit. While out, track the exact units sold, split-adjusted and including subsequent hypothetical cash distributions without reinvestment. Initialise the peak from the exit day’s closing basket value, then update it only with later closes. Re-enter when the current closing value is 15% below this running high. Opening/intraday highs are excluded. Buying back above the sale value is permitted. Reference distributions never enter actual account cash.
- **Monthly trend:** construct a monthly rebalanced, target-weight portfolio total-return index from actual ETF closes, splits and cash distributions. Signal-index distributions reinvest on the ex-date; this is only a signal convention. Actual account distributions still become cash on issuer payment dates. At each completed month-end, hold ETFs if the index is strictly above its 10-month simple moving average, including that month’s close; otherwise hold cash. Equality means cash. There is no profit-target exit in this strategy.
- **Execution:** all new signals execute at the next available session’s open with A$5 per ETF order and 5bp adverse slippage. The initial trend allocation uses only the latest signal strictly before the account’s first opening trade. Prices can rebound before a pending buy or gap down before a sell; orders are still executed. Final-day orders remain pending.
- **Contributions and resets:** contributions continue identically while in cash. Peak/fixed re-entry invests affordable cash at target weights and resets cycle capital to account wealth just before buying, including accumulated contributions and any actual distribution receivables. Contributions while invested raise cycle capital; profit targets are not measured against lifetime gains after a reset.
- **Monthly purchases:** active accounts buy whole units with new cash at the first available monthly open, using allocation deficits. There are no routine sales to rebalance the actual account. The monthly rebalancing above applies only to the signal index. Fund expenses are embedded in prices; they are not deducted again.

## Signal warm-up

The inception month is excluded as a conservative stub. Ten complete monthly closes are required with the default lookback; no signal or account buys are generated before the history is sufficient. A missing VGS quote on 31 December 2014 prevents a valid mixed-portfolio month-end observation: it is omitted, that signal-index rebalance is skipped, and the consecutive-month warm-up restarts. No December value is imputed. This pre-test history issue is recorded in `trend_history.csv` and delays Vanguard readiness. The last partial cached month does not generate a signal. A new account with adequate history uses its latest already-known allocation; a new account without it stays in cash. Ready dates below indicate the first opening session after the first valid moving-average decision, which can itself be bearish.

| Portfolio | First session with sufficient trend history |
|---|---|
| NDQ | 2016-05-02 |
| Vanguard diversified | 2015-11-02 |
| Betashares diversified | 2024-04-02 |
| Betashares growth tilt | 2024-04-02 |
| Global growth tilt | 2024-04-02 |

The same-start comparison begins 2023-05-12; the warm-up-free common comparison begins 2024-04-02. The latter resets all accounts to identical starting capital on that later date, rather than carrying earlier gains forward. This isolates a comparison where every portfolio has enough signal history.

## Same start as previous study

Cash earns 0%. Wealth includes estimated terminal liquidation costs; XIRR is annualised and drawdown is adjusted for contributions. Cash days are calendar days fully out of ETF holdings, including initial warm-up where applicable. Each table crosses source-data gaps.

| Portfolio | Strategy | Wealth | Contributed | Profit | MWR/year | Max drawdown | Entries | Exits | Re-entries | Cash days | Warm-up days |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| NDQ | Buy-and-hold | 96,362 | 62,000 | 34,362 | 19.82% | -21.35% | 1 | 0 | 0 | 0 | 0 |
| NDQ | Exit 20%, stay cash | 67,488 | 62,000 | 5,488 | 3.69% | -7.38% | 1 | 1 | 0 | 1068 | 0 |
| NDQ | Exit 20%, fixed dip 15% | 67,488 | 62,000 | 5,488 | 3.69% | -7.38% | 1 | 1 | 0 | 1068 | 0 |
| NDQ | Exit 20%, peak dip 15% | 91,234 | 62,000 | 29,234 | 17.27% | -9.19% | 3 | 3 | 2 | 973 | 0 |
| NDQ | 10-month trend | 83,148 | 62,000 | 21,148 | 13.00% | -13.33% | 3 | 2 | 2 | 122 | 0 |
| Vanguard diversified | Buy-and-hold | 85,833 | 62,000 | 23,833 | 14.46% | -13.55% | 1 | 0 | 0 | 0 | 0 |
| Vanguard diversified | Exit 20%, stay cash | 69,007 | 62,000 | 7,007 | 4.66% | -7.33% | 1 | 1 | 0 | 852 | 0 |
| Vanguard diversified | Exit 20%, fixed dip 15% | 69,007 | 62,000 | 7,007 | 4.66% | -7.33% | 1 | 1 | 0 | 852 | 0 |
| Vanguard diversified | Exit 20%, peak dip 15% | 69,007 | 62,000 | 7,007 | 4.66% | -7.33% | 1 | 1 | 0 | 852 | 0 |
| Vanguard diversified | 10-month trend | 75,864 | 62,000 | 13,864 | 8.86% | -13.53% | 4 | 3 | 3 | 123 | 0 |
| Betashares diversified | Buy-and-hold | 86,415 | 62,000 | 24,415 | 14.77% | -13.60% | 1 | 0 | 0 | 0 | 0 |
| Betashares diversified | Exit 20%, stay cash | 69,102 | 62,000 | 7,102 | 4.72% | -7.01% | 1 | 1 | 0 | 852 | 0 |
| Betashares diversified | Exit 20%, fixed dip 15% | 69,102 | 62,000 | 7,102 | 4.72% | -7.01% | 1 | 1 | 0 | 852 | 0 |
| Betashares diversified | Exit 20%, peak dip 15% | 69,102 | 62,000 | 7,102 | 4.72% | -7.01% | 1 | 1 | 0 | 852 | 0 |
| Betashares diversified | 10-month trend | 70,438 | 62,000 | 8,438 | 5.57% | -13.59% | 3 | 2 | 2 | 419 | 326 |
| Betashares growth tilt | Buy-and-hold | 89,261 | 62,000 | 27,261 | 16.26% | -15.80% | 1 | 0 | 0 | 0 | 0 |
| Betashares growth tilt | Exit 20%, stay cash | 67,843 | 62,000 | 5,843 | 3.92% | -7.10% | 1 | 1 | 0 | 991 | 0 |
| Betashares growth tilt | Exit 20%, fixed dip 15% | 67,843 | 62,000 | 5,843 | 3.92% | -7.10% | 1 | 1 | 0 | 991 | 0 |
| Betashares growth tilt | Exit 20%, peak dip 15% | 79,028 | 62,000 | 17,028 | 10.70% | -7.10% | 2 | 2 | 1 | 823 | 0 |
| Betashares growth tilt | 10-month trend | 73,896 | 62,000 | 11,896 | 7.69% | -8.79% | 3 | 2 | 2 | 448 | 326 |
| Global growth tilt | Buy-and-hold | 92,108 | 62,000 | 30,108 | 17.71% | -15.97% | 1 | 0 | 0 | 0 | 0 |
| Global growth tilt | Exit 20%, stay cash | 68,163 | 62,000 | 6,163 | 4.12% | -7.22% | 1 | 1 | 0 | 1011 | 0 |
| Global growth tilt | Exit 20%, fixed dip 15% | 68,163 | 62,000 | 6,163 | 4.12% | -7.22% | 1 | 1 | 0 | 1011 | 0 |
| Global growth tilt | Exit 20%, peak dip 15% | 79,310 | 62,000 | 17,310 | 10.86% | -7.22% | 2 | 2 | 1 | 843 | 0 |
| Global growth tilt | 10-month trend | 74,519 | 62,000 | 12,519 | 8.07% | -15.98% | 3 | 2 | 2 | 418 | 326 |

Exit 20%, peak dip 15% beat buy-and-hold on final wealth in 0 of 5 portfolios. It completed 4 re-entries. These portfolios share underlying holdings and market periods; they are not independent observations.
10-month trend beat buy-and-hold on final wealth in 0 of 5 portfolios. It completed 11 re-entries. These portfolios share underlying holdings and market periods; they are not independent observations.

## All portfolios have enough trend history

Cash earns 0%. Wealth includes estimated terminal liquidation costs; XIRR is annualised and drawdown is adjusted for contributions. Cash days are calendar days fully out of ETF holdings, including initial warm-up where applicable. Each table crosses source-data gaps.

| Portfolio | Strategy | Wealth | Contributed | Profit | MWR/year | Max drawdown | Entries | Exits | Re-entries | Cash days | Warm-up days |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| NDQ | Buy-and-hold | 65,879 | 51,000 | 14,879 | 14.72% | -21.40% | 1 | 0 | 0 | 0 | 0 |
| NDQ | Exit 20%, stay cash | 57,115 | 51,000 | 6,115 | 6.36% | -10.86% | 1 | 1 | 0 | 698 | 0 |
| NDQ | Exit 20%, fixed dip 15% | 64,417 | 51,000 | 13,417 | 13.38% | -10.86% | 2 | 2 | 1 | 645 | 0 |
| NDQ | Exit 20%, peak dip 15% | 76,323 | 51,000 | 25,323 | 23.77% | -10.86% | 3 | 3 | 2 | 603 | 0 |
| NDQ | 10-month trend | 57,438 | 51,000 | 6,438 | 6.68% | -13.38% | 3 | 2 | 2 | 122 | 0 |
| Vanguard diversified | Buy-and-hold | 62,696 | 51,000 | 11,696 | 11.78% | -13.58% | 1 | 0 | 0 | 0 | 0 |
| Vanguard diversified | Exit 20%, stay cash | 58,858 | 51,000 | 7,858 | 8.09% | -13.58% | 1 | 1 | 0 | 390 | 0 |
| Vanguard diversified | Exit 20%, fixed dip 15% | 58,858 | 51,000 | 7,858 | 8.09% | -13.58% | 1 | 1 | 0 | 390 | 0 |
| Vanguard diversified | Exit 20%, peak dip 15% | 58,858 | 51,000 | 7,858 | 8.09% | -13.58% | 1 | 1 | 0 | 390 | 0 |
| Vanguard diversified | 10-month trend | 57,032 | 51,000 | 6,032 | 6.28% | -13.58% | 3 | 2 | 2 | 93 | 0 |
| Betashares diversified | Buy-and-hold | 63,279 | 51,000 | 12,279 | 12.32% | -13.63% | 1 | 0 | 0 | 0 | 0 |
| Betashares diversified | Exit 20%, stay cash | 58,829 | 51,000 | 7,829 | 8.06% | -13.63% | 1 | 1 | 0 | 396 | 0 |
| Betashares diversified | Exit 20%, fixed dip 15% | 58,829 | 51,000 | 7,829 | 8.06% | -13.63% | 1 | 1 | 0 | 396 | 0 |
| Betashares diversified | Exit 20%, peak dip 15% | 58,829 | 51,000 | 7,829 | 8.06% | -13.63% | 1 | 1 | 0 | 396 | 0 |
| Betashares diversified | 10-month trend | 57,165 | 51,000 | 6,165 | 6.41% | -13.63% | 3 | 2 | 2 | 93 | 0 |
| Betashares growth tilt | Buy-and-hold | 64,055 | 51,000 | 13,055 | 13.05% | -15.81% | 1 | 0 | 0 | 0 | 0 |
| Betashares growth tilt | Exit 20%, stay cash | 58,620 | 51,000 | 7,620 | 7.86% | -15.81% | 1 | 1 | 0 | 420 | 0 |
| Betashares growth tilt | Exit 20%, fixed dip 15% | 58,620 | 51,000 | 7,620 | 7.86% | -15.81% | 1 | 1 | 0 | 420 | 0 |
| Betashares growth tilt | Exit 20%, peak dip 15% | 58,620 | 51,000 | 7,620 | 7.86% | -15.81% | 1 | 1 | 0 | 420 | 0 |
| Betashares growth tilt | 10-month trend | 59,815 | 51,000 | 8,815 | 9.02% | -8.81% | 3 | 2 | 2 | 122 | 0 |
| Global growth tilt | Buy-and-hold | 65,252 | 51,000 | 14,252 | 14.15% | -16.01% | 1 | 0 | 0 | 0 | 0 |
| Global growth tilt | Exit 20%, stay cash | 57,822 | 51,000 | 6,822 | 7.07% | -16.01% | 1 | 1 | 0 | 472 | 0 |
| Global growth tilt | Exit 20%, fixed dip 15% | 57,822 | 51,000 | 6,822 | 7.07% | -16.01% | 1 | 1 | 0 | 472 | 0 |
| Global growth tilt | Exit 20%, peak dip 15% | 57,822 | 51,000 | 6,822 | 7.07% | -16.01% | 1 | 1 | 0 | 472 | 0 |
| Global growth tilt | 10-month trend | 60,285 | 51,000 | 9,285 | 9.48% | -16.01% | 3 | 2 | 2 | 92 | 0 |

Exit 20%, peak dip 15% beat buy-and-hold on final wealth in 1 of 5 portfolios. It completed 2 re-entries. These portfolios share underlying holdings and market periods; they are not independent observations.
10-month trend beat buy-and-hold on final wealth in 0 of 5 portfolios. It completed 10 re-entries. These portfolios share underlying holdings and market periods; they are not independent observations.

## What the results mean

Peak-based re-entry addresses the old rule’s dependence on the original sale price. It can re-enter following a correction even when the market is still above that sale. It still caps gains at each 20% exit and can remain in cash while prices rise. The profit target provides no downside protection before it is reached. A completed re-entry can be followed by further losses.

The monthly trend rule allows winners to continue beyond 20% and changes allocation only after a month-end signal. It reacts with a lag, can sell after a substantial decline, can miss a fast rebound, and can repeatedly buy and sell in sideways markets. Cash exposure and lower observed drawdown are not guarantees of capital protection. The same-start BGBL trend results include a long warm-up in cash; compare the second table to assess outcomes without that initial-history difference.

These are illustrative rules inspired by systematic investing, not replicas of AQR, Man AHL or any named fund. No parameter optimisation or claim of the best rule is made.

## Different market conditions

Selected 12-month accounts beginning January 2020 or January 2022, 0% cash. BGBL funds have no history in these periods and are omitted. These examples are not pooled with common-period results.

| Entry | Portfolio | Strategy | Wealth | Contributed | MWR/year | Max drawdown | Exits | Re-entries |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2020-01-02 | NDQ | Buy-and-hold | 39,303 | 31,000 | 33.06% | -20.81% | 0 | 0 |
| 2020-01-02 | NDQ | Exit 20%, stay cash | 36,955 | 31,000 | 23.64% | -20.81% | 1 | 0 |
| 2020-01-02 | NDQ | Exit 20%, fixed dip 15% | 36,955 | 31,000 | 23.64% | -20.81% | 1 | 0 |
| 2020-01-02 | NDQ | Exit 20%, peak dip 15% | 36,955 | 31,000 | 23.64% | -20.81% | 1 | 0 |
| 2020-01-02 | NDQ | 10-month trend | 39,303 | 31,000 | 33.06% | -20.81% | 0 | 0 |
| 2022-01-04 | NDQ | Buy-and-hold | 23,801 | 31,000 | -28.19% | -30.96% | 0 | 0 |
| 2022-01-04 | NDQ | Exit 20%, stay cash | 23,801 | 31,000 | -28.19% | -30.96% | 0 | 0 |
| 2022-01-04 | NDQ | Exit 20%, fixed dip 15% | 23,801 | 31,000 | -28.19% | -30.96% | 0 | 0 |
| 2022-01-04 | NDQ | Exit 20%, peak dip 15% | 23,801 | 31,000 | -28.19% | -30.96% | 0 | 0 |
| 2022-01-04 | NDQ | 10-month trend | 28,054 | 31,000 | -11.64% | -20.20% | 1 | 0 |
| 2020-01-02 | Vanguard diversified | Buy-and-hold | 32,589 | 31,000 | 6.27% | -26.94% | 0 | 0 |
| 2020-01-02 | Vanguard diversified | Exit 20%, stay cash | 32,589 | 31,000 | 6.27% | -26.94% | 0 | 0 |
| 2020-01-02 | Vanguard diversified | Exit 20%, fixed dip 15% | 32,589 | 31,000 | 6.27% | -26.94% | 0 | 0 |
| 2020-01-02 | Vanguard diversified | Exit 20%, peak dip 15% | 32,589 | 31,000 | 6.27% | -26.94% | 0 | 0 |
| 2020-01-02 | Vanguard diversified | 10-month trend | 29,673 | 31,000 | -5.21% | -26.94% | 1 | 1 |
| 2022-01-04 | Vanguard diversified | Buy-and-hold | 28,804 | 31,000 | -8.69% | -18.41% | 0 | 0 |
| 2022-01-04 | Vanguard diversified | Exit 20%, stay cash | 28,804 | 31,000 | -8.69% | -18.41% | 0 | 0 |
| 2022-01-04 | Vanguard diversified | Exit 20%, fixed dip 15% | 28,804 | 31,000 | -8.69% | -18.41% | 0 | 0 |
| 2022-01-04 | Vanguard diversified | Exit 20%, peak dip 15% | 28,804 | 31,000 | -8.69% | -18.41% | 0 | 0 |
| 2022-01-04 | Vanguard diversified | 10-month trend | 28,313 | 31,000 | -10.62% | -13.06% | 2 | 2 |

## Rolling 12-month accounts after common signal readiness

Monthly entry cohorts, main study, 0% cash. Complete and gap-affected windows are separated. Overlapping accounts are dependent; hit counts and win counts are descriptive, not future probabilities. Median drawdown can mask more severe losses in individual trials.

| Portfolio | Strategy | Gap affected | Accounts | Beat hold | Median wealth vs hold | Median drawdown | Worst drawdown | Median cash days |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Betashares diversified | Exit 20%, peak dip 15% | False | 6 | 0 | 0 | -13.64% | -13.67% | 0.0 |
| Betashares diversified | Exit 20%, peak dip 15% | True | 14 | 0 | 0 | -8.94% | -13.78% | 0.0 |
| Betashares diversified | 10-month trend | False | 6 | 0 | -1,568 | -13.64% | -13.67% | 32.0 |
| Betashares diversified | 10-month trend | True | 14 | 0 | -1,380 | -8.94% | -13.78% | 32.0 |
| Betashares growth tilt | Exit 20%, peak dip 15% | False | 6 | 0 | 0 | -15.84% | -15.86% | 0.0 |
| Betashares growth tilt | Exit 20%, peak dip 15% | True | 14 | 0 | 0 | -10.27% | -15.89% | 0.0 |
| Betashares growth tilt | 10-month trend | False | 6 | 0 | -1,762 | -8.81% | -8.84% | 62.0 |
| Betashares growth tilt | 10-month trend | True | 14 | 2 | -1,168 | -6.80% | -8.85% | 61.0 |
| Global growth tilt | Exit 20%, peak dip 15% | False | 6 | 1 | 0 | -16.01% | -16.04% | 0.0 |
| Global growth tilt | Exit 20%, peak dip 15% | True | 14 | 1 | 0 | -11.40% | -16.40% | 0.0 |
| Global growth tilt | 10-month trend | False | 6 | 0 | -1,807 | -16.01% | -16.04% | 32.0 |
| Global growth tilt | 10-month trend | True | 14 | 0 | -1,364 | -8.97% | -16.40% | 46.0 |
| NDQ | Exit 20%, peak dip 15% | False | 6 | 2 | 0 | -18.18% | -21.43% | 30.0 |
| NDQ | Exit 20%, peak dip 15% | True | 14 | 5 | 0 | -15.18% | -21.46% | 13.0 |
| NDQ | 10-month trend | False | 6 | 0 | -2,383 | -13.38% | -13.40% | 62.0 |
| NDQ | 10-month trend | True | 14 | 1 | -2,186 | -12.96% | -13.41% | 61.0 |
| Vanguard diversified | Exit 20%, peak dip 15% | False | 6 | 0 | 0 | -13.58% | -13.59% | 0.0 |
| Vanguard diversified | Exit 20%, peak dip 15% | True | 14 | 0 | 0 | -9.06% | -13.65% | 0.0 |
| Vanguard diversified | 10-month trend | False | 6 | 0 | -1,473 | -13.58% | -13.59% | 32.0 |
| Vanguard diversified | 10-month trend | True | 14 | 0 | -1,295 | -9.06% | -13.65% | 32.0 |

## Hypothetical 3% cash sensitivity

Common-ready accounts. This is a constant assumed nominal yield, not historical deposit rates. Buy-and-hold at the same rate remains the paired baseline.

| Portfolio | Strategy | Wealth | Wealth vs same-rate hold | Max drawdown |
|---|---|---:|---:|---:|
| NDQ | Buy-and-hold | 65,884 | 0 | -21.40% |
| NDQ | Exit 20%, peak dip 15% | 79,511 | 13,628 | -10.86% |
| NDQ | 10-month trend | 57,880 | -8,004 | -13.38% |
| Vanguard diversified | Buy-and-hold | 62,708 | 0 | -13.57% |
| Vanguard diversified | Exit 20%, peak dip 15% | 60,546 | -2,162 | -13.57% |
| Vanguard diversified | 10-month trend | 57,395 | -5,312 | -13.57% |
| Betashares diversified | Buy-and-hold | 63,290 | 0 | -13.62% |
| Betashares diversified | Exit 20%, peak dip 15% | 60,538 | -2,752 | -13.62% |
| Betashares diversified | 10-month trend | 57,522 | -5,768 | -13.62% |
| Betashares growth tilt | Buy-and-hold | 64,071 | 0 | -15.82% |
| Betashares growth tilt | Exit 20%, peak dip 15% | 60,416 | -3,655 | -15.82% |
| Betashares growth tilt | 10-month trend | 60,292 | -3,778 | -8.81% |
| Global growth tilt | Buy-and-hold | 65,266 | 0 | -16.01% |
| Global growth tilt | Exit 20%, peak dip 15% | 59,773 | -5,493 | -16.01% |
| Global growth tilt | 10-month trend | 60,656 | -4,611 | -16.01% |

## Files and limitations

`trials.csv` includes every full-history, annual-start, monthly 3/6/12/24-month and quarterly 36/60-month account plus both common starts, including the supplemental A$10,000 study. Only complete rolling horizons are included. `summary.csv` separates `all_available` from `common_ready_entries` cohorts; they overlap and must not be pooled. `common_daily.csv` includes portfolio state, cycle capital and reference peaks for both main common windows. `trend_history.csv` provides month-end signal values and moving averages. This index is constructed from actual ETF returns for signals; it is not an actual fund or a proxy extending pre-inception history.

`trade_ledger.csv` and `cycles.csv` retain full/common/common-ready accounts and selected NDQ January 2018/2020/2022 rolling examples. Initial trend entries following warm-up use `entry_fill`; later purchases after an exit use `reentry_fill`. Entries include the initial investment; re-entries exclude it. `signal_date`/`exit_date` refer to the first exit. The legacy `time_to_target_days` field is not applicable to trend allocation. Charts are in `wealth_*.svg`; identical lines can overlap.

All results exclude personal CGT, income tax, franking-credit benefits, AMIT cost-base changes and inflation. Trading more often can create additional taxable gains. Brokerage/slippage, liquidity and immediately available sale proceeds are assumptions; settlement or broker rules may defer a rapid re-entry. Signal-index ex-date reinvestment is a mathematical convention, not an assertion that actual distributions were spendable before payment. Individual ETFs, allocations and thresholds were selected retrospectively. The short common-ready history does not establish performance over a full market cycle. Future losses may exceed all observed drawdowns.

Every trial is checked by rebuilding cash, final holdings, distribution receivables, order prices and costs from events. Initial trend decisions use only earlier completed month-end signals. Runtime checks enforce next-available-session execution. Tests cover warm-up, future-data independence, equality, distributions, splits, peak anchors and repeated cycles. Input/output hashes and validation results are saved alongside this report.
