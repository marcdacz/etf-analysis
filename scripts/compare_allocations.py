"""Reproducible buy-and-hold allocation comparison using the existing ETF engine."""
import csv
import json
from pathlib import Path
from etf_backtest.analysis import prepare_data
from etf_backtest.engine import simulate

ROOT = Path(__file__).resolve().parents[1]
ALLOCATIONS = [
    ("BGBL 70 / NDQ 30", {"BGBL": 0.7, "NDQ": 0.3}),
    ("BGBL 50 / NDQ 50", {"BGBL": 0.5, "NDQ": 0.5}),
    ("BGBL 30 / NDQ 70", {"BGBL": 0.3, "NDQ": 0.7}),
]
STARTS = ("2023-05-12", "2024-04-02")
def main():
    config = json.loads((ROOT / "config.json").read_text())
    prices, distributions, _, gaps, _ = prepare_data(ROOT, config)
    rows = []
    for start in STARTS:
        for label, weights in ALLOCATIONS:
            result, _, _ = simulate(
                prices, distributions, weights, start, config["end"],
                config, target=None, cash_rate=0.0,
            )
            rows.append({
                "start": result["start"], "end": result["end"],
                "allocation": label,
                "contributions": result["contributed_capital"],
                "final_wealth": result["final_wealth"],
                "profit": result["profit"],
                "money_weighted_return": result["money_weighted_return"],
                "maximum_drawdown": result["maximum_drawdown"],
                "missing_sessions_in_period": sum(result["start"] <= d <= result["end"] for d in gaps),
            })
    output = ROOT / "results" / "allocation_comparison.csv"
    output.parent.mkdir(exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} allocation comparison results to {output}")

if __name__ == "__main__":
    main()
