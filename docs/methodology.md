# How the tests work

> **TL;DR:** every strategy gets the same deposits, pays the same trading costs and trades after its signal is known. We use actual ETF history, keep distributions separate from prices and leave missing data visible.

[Overview](../README.md) · [Run the project](running.md)

## Portfolios

| Portfolio | Starting weights | What it compares |
| --- | --- | --- |
| NDQ | 100% NDQ | Nasdaq exposure on its own |
| VAS / VGS | 30% / 70% | Australian and international shares |
| A200 / BGBL | 30% / 70% | A similar mix using Betashares funds |
| A200 / BGBL / NDQ | 20% / 50% / 30% | A broader mix with extra Nasdaq exposure |
| BGBL / NDQ | 70% / 30% | International shares with extra Nasdaq exposure |

A200 and VAS are not identical funds. Neither are BGBL and VGS. Their holdings and results can differ. Adding NDQ to a global share fund also increases exposure to companies that may already be in that fund.

A separate study starts with A$10,000 and tests VAS alone, VGS alone and 30/70 VAS/VGS. Those results are in the CSV files under `study=supplemental`. The main reader pages use the A$20,000 study.

## Shared assumptions

| Setting | Saved value |
| --- | --- |
| Currency | Australian dollars |
| Starting money | A$20,000 |
| Regular deposit | A$1,000 on the first available trading day of each later month |
| First month | The starting amount replaces that month's regular deposit |
| Brokerage | A$5 for each ETF order |
| Price allowance for trading | 0.05% worse than the opening price for each buy or sale |
| Units | Whole units; leftover money stays in cash |
| Cash return | 0% in the reader tables; a separate test assumes a constant 3% a year |
| Distributions | Earned by holders before ex-date opening trades; spendable on the payment date |
| Taxes | Excluded; no personal tax model is included |

The 3% cash return is an assumption, not a record of bank rates. Fund fees are already reflected in observed prices and distributions, so we do not subtract them again.

## Dates and deposits

| Comparison | Period | Total money added per main account | Why use it? |
| --- | --- | --- | --- |
| Original shared start | 12 May 2023 to 16 November 2026 | A$62,000 | All five portfolios have observed ETF trading data. |
| Shared start after trend history is ready | 2 April 2024 to 16 November 2026 | A$51,000 | Every portfolio has enough monthly data for the trend signal. |

Each row starts a new account with A$20,000. The April 2024 accounts do not inherit earlier gains. Raw balances from different periods are not directly comparable.

We also test each portfolio's longer available history, annual starting dates, monthly 3, 6, 12 and 24-month periods, and quarterly 3 and 5-year periods. A period is included only if its full length is available. These tests overlap, so their results are not independent observations.

BGBL has no actual history for the COVID fall or the 2022 sell-off. We do not fill those years with another fund or an invented return series.

## Gain targets

For the first investment round:

```text
gain = account value after estimated selling costs / total money added - 1
```

Account value includes ETF holdings, cash and distributions already earned but not yet paid. Deposits are capital, not profit. For example, A$11,500 against A$10,000 added is a 15% gain. Adding another A$1,000 changes the gain to about 13.64%, before any price move.

For the repeated trading rules, each new round starts from the account value just before buying back. That includes cash saved while waiting, earlier profits and any real unpaid distributions. The next 20% target uses this new starting value plus later deposits while invested.

## Trade timing and cash

A closing signal leads to an order at the **next available session's open**, including trading costs. The test does not trade at the same closing price that generated the signal. A final-day order is left pending.

While invested, regular deposits and spare cash buy units monthly, using cash to move toward the target weights. There are no routine sales just to reset the actual account's weights. While waiting to buy back, deposits stay in cash.

The model treats sale proceeds as available straight away. A real broker may require settlement or extra cash before allowing a quick purchase. Prices can also gap between signal and execution, so a sale triggered at a 20% gain can finish below that gain.

## Prices, distributions and splits

The ex-date is the first day a new buyer no longer gets that payout. The payment date is when the cash becomes available.

- Prices come from Yahoo Finance; cash distributions and payment dates come from the fund issuers. [Source URLs and file hashes](../data/raw/manifest.json).
- The account uses prices without distribution adjustments and adds actual distributions separately. This avoids counting the same payout twice.
- Yahoo's historical price quotes account for splits. The loader reverses that split adjustment to get the prices at the time, then the account changes its units on a split date.
- The saved actual ETF series have no split events. Separate tests use made-up numbers to check split handling. Those numbers never enter historical results.
- Issuer cash amounts and dates take priority when they disagree with Yahoo events. Franking credits and other tax amounts are not treated as spendable cash. [Data checks](../data/normalized/audit.json).

## The trend signal

The 10-month rule uses a separate index built from actual ETF returns. It includes distributions as if they were reinvested on the ex-date, and resets its weights monthly. This is a way to measure the market trend. It is not a fund, a replacement for missing pre-launch history or the real account balance.

The real account still gets distributions on their actual payment dates and pays costs when it trades.

We exclude the first, possibly incomplete month of history. The rule needs ten complete month-end observations. At each later month-end, it holds ETFs when the index is strictly above the average of those ten values; otherwise it holds cash. A new account uses only a decision made before its first opening trade. Without enough history, it waits in cash.

## Missing data

| Missing date | How we handle it | What it can affect |
| --- | --- | --- |
| 10 May 2024 | Omit the session consistently across strategies; flag periods that cross it. | Signals, execution timing and the biggest recorded fall. |
| 24 October 2025 | The same; zero-volume placeholder quotes are also excluded. | The same. |
| 31 December 2014, VGS | Omit that month-end signal value, skip its signal-index rebalance and restart the monthly lookback. | Earlier trend readiness, including VAS/VGS and VGS on its own. |

We do not carry prices forward or invent missing closes. Two prices on either side of a gap are connected in the line charts; no extra price observation is added.

The earlier VGS gap appears in [the signal history](../results/tactical/trend_history.csv). The two trading-session gaps appear in [the original data-gap record](../results/data_gaps.json) and in the later studies' validation files. Read the results as estimates with these known limits.

## Reading the numbers

| Measure | What it means |
| --- | --- |
| Final value | Cash, ETF holdings and earned unpaid distributions, after estimated costs to sell the remaining holdings. |
| Money added | Starting money plus later deposits. |
| Profit | Final value minus money added. |
| Annual return | Money-weighted return, calculated from dated deposits and final value. It can look extreme over short periods. |
| Biggest fall | Maximum drawdown of a return index that adjusts for deposits. New deposits do not hide a loss. |
| Days to target | Days until the first profit-target signal. It is not used for the trend strategy. |
| Sales / exits | Completed sales caused by a signal. An estimated end value is not counted as an extra sale. |
| Times bought back | Completed purchases after a sale. The first investment is excluded. |
| Days in cash | Calendar days fully out of ETF holdings, including trend warm-up where it applies. |

## What the tests cannot tell us

The checks confirm the account maths and saved file contents. They do not independently confirm every price supplied by a provider.

These results are before personal income tax, capital gains tax and inflation. They also leave out personal tax credits and cost-base changes. Repeated sales may have a different after-tax result from holding.

We chose the ETFs and rules knowing which funds exist today. The tests have missing prices, short histories for newer funds and assumed trading costs. Settings were not selected through a search for the best backtest, and these simple rules do not copy a named manager's fund.

No result here puts a limit on future losses or proves which strategy will work next.
