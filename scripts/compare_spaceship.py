"""Compare Spaceship Universe unit-price history with NDQ on common dates.

Requires a sourced CSV at data/external/spaceship_universe.csv containing
date,unit_price and optionally distribution_per_unit. The Spaceship unit
price must be an actual AUD NAV, not a stock proxy or interpolated series.\nThis is a PRICE-ONLY comparison; distributions are not included for either fund.
"""
import csv
import json
from pathlib import Path
from etf_backtest.analysis import prepare_data
from etf_backtest.engine import xirr
from datetime import date
import math

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/external/spaceship_universe.csv"
OUT = ROOT / "results/spaceship_vs_ndq.csv"
WEIGHTS = {"NDQ only": (1,0), "Universe only": (0,1),
           "NDQ 70 / Universe 30": (.7,.3),
           "NDQ 50 / Universe 50": (.5,.5),
           "NDQ 30 / Universe 70": (.3,.7)}

def read_universe(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing verified Spaceship Universe unit-price CSV: {path}. No proxy data will be used.")
    result = {}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        if not {"date","unit_price"} <= set(reader.fieldnames or []):
            raise ValueError("Spaceship CSV must have date,unit_price columns")
        for row in reader:
            d = date.fromisoformat(row["date"]).isoformat()
            price = float(row["unit_price"])
            if not math.isfinite(price) or price <= 0 or d in result:
                raise ValueError(f"Invalid or duplicate Universe unit price on {d}")
            dist = float(row.get("distribution_per_unit") or 0)
            if not math.isfinite(dist) or dist < 0:
                raise ValueError(f"Invalid distribution on {d}")
            result[d] = (price, dist)
    if len(result) < 30:
        raise ValueError("Insufficient Spaceship unit-price observations")
    return result

def run(prices, distributions, start, end, ndq_weight, universe_weight, config):
    days = sorted(d for d in prices if start <= d <= end)
    cash = 0.
    units = [0.,0.]
    contributions = 0.
    fees = 0.
    flows = []
    previous_month = None
    peak = 1.
    index = 1.
    prior_wealth = None
    maxdd = 0.
    for d in days:
        ndq_close, universe_close, ndq_dist, universe_dist = prices[d]
        month = d[:7]
        added = (config["initial_capital"] if previous_month is None else
                 config["monthly_contribution"] if month != previous_month else 0.)
        if added:
            cash += added
            contributions += added
            flows.append((date.fromisoformat(d), -added))
        # Distribution entries must be actual per-unit cash distributions,
        # not adjusted-price changes; credited and reinvested at this close.
        # Price-only: do not add distributions for one fund but not the other.
        if added:
            available = cash
            for i,(weight,price) in enumerate(((ndq_weight,ndq_close),(universe_weight,universe_close))):
                if not weight:
                    continue
                budget = available * weight
                if budget > config["brokerage"]:
                    qty = math.floor((budget-config["brokerage"]) / (price*(1+config["slippage"]))) if i == 0 else (budget-config["brokerage"]) / (price*(1+config["slippage"]))
                    if qty > 0:
                        cost = qty*price*(1+slippage)+brokerage
                        cash -= cost
                        units[i] += qty
                        fees += brokerage
        wealth = cash + units[0]*ndq_close + units[1]*universe_close
        if prior_wealth is None:
            index = wealth/contributions
        else:
            index *= wealth/(prior_wealth+added)
        peak = max(peak,index)
        maxdd = min(maxdd,index/peak-1)
        prior_wealth = wealth
        previous_month = month
    flows.append((date.fromisoformat(days[-1]),wealth))
    return dict(start=days[0],end=days[-1],contributions=contributions,
                final_wealth=wealth,profit=wealth-contributions,
                money_weighted_return=xirr(flows),maximum_drawdown=maxdd,
                brokerage_paid=fees)

def main():
    config = json.loads((ROOT/"config.json").read_text())
    ndq_prices, _, _, gaps, _ = prepare_data(ROOT,config)
    universe = read_universe(SOURCE)
    # Align by intersection; do not forward-fill absent NAVs.
    ndq = ndq_prices["NDQ"]
    common = sorted(set(ndq) & set(universe))
    if len(common) < 30:
        raise ValueError("Insufficient common dates between NDQ and Universe")
    aligned = {d:(ndq[d]["close"],universe[d][0],0.,0.) for d in common}
    rows = []
    for start in dict.fromkeys((common[0],"2023-05-12","2024-04-02")):
        if start > min(config["end"], common[-1]):
            continue
        for label,(n,u) in WEIGHTS.items():
            result = run(aligned, None,start, min(config["end"],common[-1]),n,u,config)
            rows.append(dict(allocation=label,return_basis="PRICE ONLY; excludes distributions and Spaceship platform fees",**result))
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w",newline="") as f:
        writer = csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT}")

if __name__ == "__main__":
    main()
