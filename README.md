# ETF accumulation backtests

A local, pre-tax Python study of accumulating ETFs, then selling the entire portfolio at a 15% or 20% gain. Uses actual ETF prices and issuer distributions; no proxy history. Results include explicitly flagged source-data gaps.

## Setup and run

Python 3.10+ and system `curl` are sufficient. No Python dependencies or API keys are required.

```sh
cd /Users/marcdacz/src/etf-analysis
python3 -m unittest discover -s tests -v
python3 -m etf_backtest all        # cached sources reused; downloads only missing files
python3 -m etf_backtest run        # entirely offline from normalized CSVs
python3 -m etf_backtest validate   # verify pinned inputs and reconcile cash ledgers
python3 -m etf_backtest fetch --refresh  # explicitly replace source snapshot, then normalize
```

Edit `config.json` for dates, capital, contributions, costs, cash-rate sensitivities and portfolio weights. Run `all` after extending dates so normalized files are regenerated. Raw downloads cover the provider's latest 15-year window; dates before cached coverage are not extrapolated. Commands run from the repository root. `--config path.json` selects an alternative configuration.

## Confirmed comparisons

Main: A$20,000 initially, A$1,000 monthly from the following month. Portfolios: NDQ; 30/70 VAS/VGS; 30/70 A200/BGBL; 20/50/30 A200/BGBL/NDQ; 70/30 BGBL/NDQ. Supplemental: A$10,000, VAS, VGS and 30/70 VAS/VGS. All use buy-and-hold and 15%/20% exits, stay in cash after exit, and continue identical contributions. Cash earns 0% or a hypothetical constant 3% annually.

Gain is `(ETF liquidation value + cash + earned unpaid distributions) / total external contributions - 1`. Contributions are capital, not profit: they dilute existing percentage gains. Signals use closing prices; sales use the following available session's open. Overnight price changes can produce a realised gain below the target. A final-day signal stays pending. Maximum one exit per trial; no stop-loss or re-entry.

Whole-unit purchases occur initially and monthly; new cash is allocated in proportion to target allocation deficits. A$5 per ETF order and 5bp adverse slippage; no routine sales to rebalance. Distribution entitlement precedes ex-date opening trades, cash becomes available on the actual payment date, and cash is reinvested at scheduled purchases. Prices exclude distribution adjustments, preventing double counting. Fund fees are already embedded. Splits are processed explicitly after reversing Yahoo's historical split adjustment.

Monthly 3/6/12/24-month and quarterly 36/60-month cohorts use only complete windows. Full-history and annual-start trials provide longer market exposure; common-period trials start when all five ETFs have observed data. BGBL's short history is never extended synthetically. Results are pre-tax; personal tax modelling is not implemented.

## Outputs

- [Plain-English report](results/report.md): results, accounting, trade-offs and limitations.
- `results/trials.csv`: all metrics, paired wealth difference vs hold, missing-data flags.
- `results/summary.csv`: common-period rolling cohorts, separated by missing-data status.
- `results/common_daily.csv`, `trade_ledger.csv`: wealth paths and full/common event audit.
- `results/wealth_*.svg`: portable charts; `data_gaps.json`: omitted dates.
- `data/raw/manifest.json`, `results/run_manifest.json`: source URLs and SHA-256 provenance.

**Data qualification:** Yahoo has missing records on 10 May 2024 and 24 October 2025. They are omitted consistently across portfolios, never filled. Windows crossing them are flagged: signals and fills could be delayed, and drawdowns understated. Use complete-window summary rows for gap-free observations. Issuer distribution amounts/dates override discrepancies in Yahoo events, documented in `data/normalized/audit.json`. Data quality checks do not constitute independent verification of every price. No future performance guarantee.

Zero-volume quotes are excluded, including indicative records before the first observed trading session. The fair common period therefore starts on 12 May 2023. Excluded records remain in the raw cache and audit.

XIRR is annualised using dated contributions and terminal wealth net of estimated liquidation costs. Drawdown uses a contribution-adjusted return index. Overlapping entry cohorts are dependent; their hit rates are descriptive frequencies, not forecasts. The report describes further limitations.

Optional PNG exports (requires `rsvg-convert` from librsvg):

```sh
sh scripts/render_charts.sh
```

## Repeated exit and re-entry study

```sh
python3 -m etf_backtest reentry
python3 -m etf_backtest validate-reentry
```

Uses the same `config.json` portfolios, contributions, costs, dates and cached actual data. Re-entry rules are in `config_reentry.json`. Outputs are separate in `results/reentry/`, preserving the original comparison.

The confirmed rule sells at a 20% cycle gain, then waits for the exact sold basket to fall 15% below its exit-day opening market value. The reference adjusts for splits and includes hypothetical cash distributions after selling, so a distribution alone cannot trigger buying. These hypothetical distributions never enter actual account cash. The anchor excludes trading costs and is fixed at the exit, rather than tracking later highs. Signals use closes; purchases and sales occur at the next available open.

Contributions accumulate in cash while waiting. Re-entry invests available cash at the original allocations, and resets target capital to total account wealth immediately before buying, including accumulated contributions and any real distribution receivables. Contributions while invested increase cycle capital. Repeat the rule, without a stop-loss. Cash waiting time can be years; re-entry may never occur. Sale proceeds are assumed immediately available; actual settlement/broker rules could delay a rapid re-entry.

See [re-entry report](results/reentry/report.md), `trials.csv`, `cycles.csv`, `summary.csv` and `wealth_*.svg` in that directory. Complete and gap-affected windows remain separated. `never_reached_target` means the account never signalled its first exit; later unfinished cycles are visible in `cycles.csv`. The original `run` and `validate` commands still apply to the original single-exit comparison.

In the re-entry CSVs, `signal_date`, `exit_date` and `time_to_target_days` refer to the first exit. `last_exit_date` and `last_entry_date` track the latest completed fills. `cash_days` counts full calendar intervals out of ETFs; `waiting_days` describes only the current unfinished wait. Cycle records include full/common accounts and every trial that actually re-entered, identified by its start/end dates.
