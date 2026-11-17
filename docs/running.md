# Run the project

> **TL;DR:** Python 3.10+ and `curl` are enough. The saved data is included, so you can repeat the analysis offline. Run each study and its validation command, then use the linked CSVs to check the results.

[Overview](../README.md) · [How the tests work](methodology.md)

## Get started

```sh
git clone https://github.com/marcdacz/etf-analysis.git
cd etf-analysis
python3 --version
python3 -m unittest discover -s tests -v
```

There are no Python packages or API keys to install. Run commands from the repository root. The PNG chart export is optional and uses `rsvg-convert` from librsvg.

## Repeat a saved backtest

| Study | Run | Validate | Output folder |
| --- | --- | --- | --- |
| Sell at 15% or 20%, stay in cash | `python3 -m etf_backtest run` | `python3 -m etf_backtest validate` | [`results/`](../results/report.md) |
| Buy back 15% below the sale value | `python3 -m etf_backtest reentry` | `python3 -m etf_backtest validate-reentry` | [`results/reentry/`](../results/reentry/report.md) |
| Peak-drop and 10-month trend rules | `python3 -m etf_backtest tactical` | `python3 -m etf_backtest validate-tactical` | [`results/tactical/`](../results/tactical/report.md) |

These commands use the saved, cleaned CSVs and do not need network access. They replace the outputs for that study.

Validation checks saved input hashes, account totals and the available trade logs. The latest tactical run checks every account's cash, holdings, distribution amounts, order prices, costs and trade timing. [Saved validation result](../results/tactical/validation.json).

The saved test run passed **39 tests**. The tactical comparison contains **33,940 scenarios**, and matches the earlier results for the unchanged rules. These counts include overlapping periods and both cash-return assumptions.

## Change the settings

| File | Settings |
| --- | --- |
| [`config.json`](../config.json) | Portfolios, dates, starting money, monthly deposits, costs and cash returns. |
| [`config_reentry.json`](../config_reentry.json) | Exit target, dip below the sale reference and target reset rule. |
| [`config_tactical.json`](../config_tactical.json) | Exit target, drop from the later high and monthly moving-average lookback. |

An alternative base file can be passed with `--config path.json`. The re-entry command accepts `--rules path.json`; the tactical command accepts `--tactical-rules path.json`.

The reader pages describe the saved snapshot through **16 November 2026**. If you change dates or settings, review the wording and date labels as well as the generated tables. Results from different starting amounts or periods should not be compared as though they were the same test.

## Download or update data

```sh
# Reuse cached source files; download only missing ones.
python3 -m etf_backtest all

# Explicitly replace the raw snapshot and rebuild the cleaned CSVs.
python3 -m etf_backtest fetch --refresh
```

Fetching needs network access. Providers can block downloads or revise data. The price request covers the provider's latest 15-year window, so refreshing later can change both the values and available history. It does not extend a fund before its actual trading history.

After updating inputs, rerun each study and its validation command. If you extend the end date, fetch and clean data for that date before running. A validation error about changed inputs means the old outputs no longer match the saved file hashes; it is a reason to rerun, not to ignore the check.

## Refresh the reader pages and charts

```sh
# Build the main README, four study READMEs and their figures from saved results.
python3 scripts/build_docs.py

# Optional: export the detailed report charts as PNGs.
sh scripts/render_charts.sh
```

The documentation script reads existing CSVs and does not run a backtest. It always writes SVG figures and also updates PNGs when `rsvg-convert` is installed. PNGs already in the repository can be viewed without installing a renderer. If PNG export was skipped, install librsvg and run the documentation script again before sharing changed figures.

The written conclusions describe this saved snapshot. After a new analysis, review them rather than assuming they still match the new results. The methodology and run guide are maintained separately.

## Find the supporting files

| File | Use it to check |
| --- | --- |
| `trials.csv` in each output folder | Every account's final value, deposits, profit, return, biggest fall and trade counts. |
| `summary.csv` | Results grouped by rule and period, with missing-data flags kept separate. |
| `trade_ledger.csv` | The retained accounts' deposits, orders and real distribution payments. |
| `cycles.csv` in re-entry and tactical outputs | Each recorded round of buying and selling. |
| `common_daily.csv` | Account values and states during the shared periods. |
| [`trend_history.csv`](../results/tactical/trend_history.csv) | Month-end index values, averages and decisions, including the early missing quote. |
| `run_manifest.json` | Settings and SHA-256 hashes for saved inputs and, in later studies, outputs. |
| `validation.json`, `independent_validation.json`, `reproducibility.json` | Saved accounting and repeat-run checks. |
| [`data/raw/manifest.json`](../data/raw/manifest.json) | Download sources, saved dates and hashes. |

The original study keeps full/shared-period trade logs. The fixed re-entry study also keeps accounts that bought back. The tactical study keeps full/shared-period accounts and selected NDQ examples from 2018, 2020 and 2022. The run checks every scenario even when its detailed trade log is not retained.

## Local files and Git

The [ignore rules](../.gitignore) cover macOS metadata, Python caches, virtual environments, coverage files, local settings and temporary downloads. They keep the historical data, results and reader figures available for repeat runs.

Adding an ignore rule does not remove an already tracked file. Existing research logs remain part of the saved snapshot.
