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
BEGIN = "<!-- allocation-comparison:start -->"
END = "<!-- allocation-comparison:end -->"

def aud(value):
    return f"A${value:,.0f}"

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

    lines = [
        BEGIN,
        "## BGBL / NDQ allocation comparison",
        "",
        "Buy-and-hold comparison using the same ETF prices, actual cash distributions, "
        "monthly contributions and trading-cost model as the other studies. "
        "These are separate accounts starting on each date, not a forecast.",
        "",
    ]
    for start in STARTS:
        subset = [r for r in rows if r["start"] >= start and r["start"][:7] == start[:7]]
        if len(subset) != 3:
            raise RuntimeError(f"Expected three comparable portfolios for {start}; got {len(subset)}")
        lines.extend([
            f"### Starting {subset[0]['start']} (through {subset[0]['end']})",
            "",
            "| Allocation | Contributions | Final value | Profit | Annualised money-weighted return | Maximum drawdown |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ])
        for r in subset:
            lines.append(
                f"| {r['allocation']} | {aud(r['contributions'])} | {aud(r['final_wealth'])} | "
                f"{aud(r['profit'])} | {r['money_weighted_return']:.1%} | {r['maximum_drawdown']:.1%} |"
            )
        lines.append("")
    lines.extend([
        "This comparison measures realised outcomes over the available BGBL history, "
        "not long-term Nasdaq superiority. BGBL already holds many Nasdaq constituents; "
        "a higher NDQ weight increases US mega-cap concentration. Missing trading sessions "
        "can affect recorded drawdowns. Taxes and inflation are excluded.",
        "",
        "[Download comparison CSV](results/allocation_comparison.csv) · "
        "[Methodology](docs/methodology.md)",
        END,
    ])
    readme = ROOT / "README.md"
    existing = readme.read_text()
    block = "\n".join(lines)
    if BEGIN in existing and END in existing:
        prefix, rest = existing.split(BEGIN, 1)
        _, suffix = rest.split(END, 1)
        updated = prefix.rstrip() + "\n\n" + block + suffix
    else:
        updated = existing.rstrip() + "\n\n" + block + "\n"
    readme.write_text(updated)
    print(f"Saved {len(rows)} results and updated README")

if __name__ == "__main__":
    main()
