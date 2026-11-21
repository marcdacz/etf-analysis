"""Fetch third-party Spaceship Universe historical unit prices.

Source is unaffiliated with Spaceship. These are PRICE observations, not
distribution-adjusted total returns. No distribution data is inferred.
"""
import csv
import json
import math
import urllib.request
from datetime import date
from pathlib import Path

URL = "https://www.spaceshipvoyagercharts.com/universe.json"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/external/spaceship_universe.csv"

def normalize(records):
    if not isinstance(records, list):
        raise ValueError("Expected JSON array")
    prices = {}
    for item in records:
        day = date.fromisoformat(item["date"][:10]).isoformat()
        price = float(item["unitPrice"])
        if not math.isfinite(price) or price <= 0:
            raise ValueError(f"Invalid price: {day}")
        if day in prices and prices[day] != price:
            raise ValueError(f"Conflicting observations: {day}")
        prices[day] = price
    if len(prices) < 100:
        raise ValueError("Too few observations")
    return sorted(prices.items())

def main():
    req = urllib.request.Request(URL, headers={"User-Agent":"etf-analysis/1.0 (historical research)"})
    with urllib.request.urlopen(req, timeout=45) as response:
        rows = normalize(json.load(response))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(("date","unit_price"))
        writer.writerows(rows)
    print(f"Downloaded {len(rows)} Universe unit prices: {rows[0][0]} through {rows[-1][0]}")
    print("WARNING: price-only series; Spaceship distributions not verified or included.")

if __name__ == "__main__":
    main()
