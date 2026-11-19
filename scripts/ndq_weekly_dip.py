"""NDQ weekly buy-and-hold: fixed DCA versus extra purchases during dips.

Signals use the previous trading session's close and its preceding 29 closes.
Orders fill at the next week's first available trading-session open.
"""
import csv
import json
import math
from collections import deque
from datetime import date
from pathlib import Path
from etf_backtest.analysis import prepare_data
from etf_backtest.engine import xirr

ROOT = Path(__file__).resolve().parents[1]
BASE_WEEKLY = 500.0
DIP_EXTRA = 100.0
DIP_THRESHOLDS = (0.05, 0.10, 0.15)
LOOKBACK = 30


def simulate_weekly(prices, distributions, start, end, config, dip_enabled, dip_threshold=0.05):
    days = sorted(d for d in prices if start <= d <= end)
    if len(days) < LOOKBACK + 1:
        raise ValueError("Not enough NDQ history for a 30-session lookback")
    # Signal at prior close, execution at first available open in each ISO week.
    units = 0
    cash = 0.0
    receivables = []
    invested = 0.0
    fees = 0.0
    slippage = 0.0
    extra_total = 0.0
    dip_weeks = 0
    buys = 0
    flows = []
    prior_closes = deque(maxlen=LOOKBACK)
    peak_index = 1.0
    return_index = 1.0
    prior_wealth = None
    worst_drawdown = 0.0
    prior_week = None
    div_by_ex = {}
    for div in distributions:
        div_by_ex.setdefault(div["ex_date"], []).append(div)
    for day in days:
        current = date.fromisoformat(day)
        week = current.isocalendar()[:2]
        # Pay any previously earned distributions before placing orders.
        for pay, amount in list(receivables):
            if pay <= day:
                cash += amount
                receivables.remove((pay, amount))
        split = prices[day]["split"]
        if split != 1:
            units *= split
        for div in div_by_ex.get(day, []):
            amount = units * div["amount"]
            if amount:
                receivables.append((div["pay_date"], amount))
        for pay, amount in list(receivables):
            if pay <= day:
                cash += amount
                receivables.remove((pay, amount))
        contribution = 0.0
        if week != prior_week:
            # Never use today's close to decide an order at today's open.
            dip = (
                dip_enabled and len(prior_closes) == LOOKBACK
                and prior_closes[-1] <= max(prior_closes) * (1 - dip_threshold)
            )
            contribution = BASE_WEEKLY + (DIP_EXTRA if dip else 0.0)
            if dip:
                dip_weeks += 1
                extra_total += DIP_EXTRA
            cash += contribution
            invested += contribution
            flows.append((current, -contribution))
            px = prices[day]["open"] * (1 + config["slippage"])
            quantity = max(0, math.floor((cash - config["brokerage"]) / px))
            if quantity:
                cash -= quantity * px + config["brokerage"]
                units += quantity
                buys += 1
                fees += config["brokerage"]
                slippage += quantity * prices[day]["open"] * config["slippage"]
        close = prices[day]["close"]
        wealth = cash + sum(a for _, a in receivables) + max(
            0.0, units * close * (1 - config["slippage"]) - (config["brokerage"] if units else 0)
        )
        if prior_wealth is None:
            return_index = wealth / invested
        else:
            return_index *= wealth / (prior_wealth + contribution)
        peak_index = max(peak_index, return_index)
        worst_drawdown = min(worst_drawdown, return_index / peak_index - 1)
        prior_wealth = wealth
        prior_week = week
        prior_closes.append(close)
    flows.append((date.fromisoformat(days[-1]), wealth))
    return dict(
        start=days[0], end=days[-1],
        strategy=f"DCA + weekly {dip_threshold:.0%} dip" if dip_enabled else "DCA only",
        dip_threshold=dip_threshold if dip_enabled else "",
        contributions=invested, extra_contributions=extra_total,
        dip_weeks=dip_weeks, buy_orders=buys,
        final_wealth=wealth, profit=wealth-invested,
        money_weighted_return=xirr(flows), maximum_drawdown=worst_drawdown,
        brokerage_paid=fees, slippage_paid=slippage,
        final_cash=cash, final_receivables=sum(a for _, a in receivables),
    )


def main():
    config = json.loads((ROOT / "config.json").read_text())
    prices, distributions, _, gaps, _ = prepare_data(ROOT, config)
    ndq = prices["NDQ"]
    # Test full available NDQ history and both existing shared comparison windows.
    starts = sorted(set([max(config["start"], min(ndq)), "2023-05-12", "2024-04-02"]))
    rows = []
    for start in starts:
        for threshold in (None, *DIP_THRESHOLDS):
            result = simulate_weekly(ndq, distributions["NDQ"], start, config["end"], config,
                                     threshold is not None, dip_threshold=threshold or 0.05)
            result["missing_sessions_in_period"] = sum(result["start"] <= d <= result["end"] for d in gaps)
            rows.append(result)
    out = ROOT / "results" / "ndq_weekly_dip_backtest.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} NDQ weekly backtest rows to {out}")
    for r in rows:
        print(f'{r["start"]}: {r["strategy"]}: contributions={r["contributions"]:.2f}, final={r["final_wealth"]:.2f}, dip_weeks={r["dip_weeks"]}')


if __name__ == "__main__":
    main()
