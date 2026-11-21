"""Regression checks for the Spaceship vs NDQ comparison."""
import csv
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from scripts.compare_spaceship import run, read_universe
from scripts.fetch_spaceship import normalize

CONFIG = {"initial_capital": 20000, "monthly_contribution": 1000,
          "brokerage": 5, "slippage": 0.0005}

class SpaceshipComparisonTests(unittest.TestCase):
    def setUp(self):
        self.prices = {
            "2024-04-02": (40.0, 2.0, 0., 0.),
            "2024-04-03": (41.0, 2.1, 0., 0.),
            "2024-05-01": (42.0, 2.2, 0., 0.),
            "2024-06-03": (43.0, 2.3, 0., 0.),
        }

    def test_all_allocations_execute_without_undefined_variables(self):
        for n,u in ((1,0),(0,1),(.7,.3),(.5,.5),(.3,.7)):
            with self.subTest(weights=(n,u)):
                result = run(self.prices, None, "2024-04-02", "2024-06-03", n,u,CONFIG)
                self.assertEqual(result["contributions"], 22000)
                self.assertGreater(result["final_wealth"], 0)
                self.assertGreaterEqual(result["brokerage_paid"], 0)

    def test_no_spaceship_brokerage(self):
        result = run(self.prices,None,"2024-04-02","2024-06-03",0,1,CONFIG)
        self.assertEqual(result["brokerage_paid"],0)

    def test_ndq_brokerage_applied(self):
        result = run(self.prices,None,"2024-04-02","2024-06-03",1,0,CONFIG)
        self.assertEqual(result["brokerage_paid"],15)

    def test_empty_date_range_fails_clearly(self):
        with self.assertRaisesRegex(ValueError,"No aligned price"):
            run(self.prices,None,"2026-01-01","2026-02-01",1,0,CONFIG)

    def test_fetch_normalization(self):
        records = [{"date":(date(2024,1,1)+timedelta(days=i)).isoformat(),
                    "unitPrice":str(1+i/100)} for i in range(100)]
        rows = normalize(records)
        self.assertEqual(len(rows),100)
        self.assertEqual(rows[0][1],1.0)

    def test_csv_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"prices.csv"
            with p.open("w",newline="") as file:
                writer=csv.writer(file)
                writer.writerow(["date","unit_price"])
                for i in range(30):
                    writer.writerow([(date(2024,1,1)+timedelta(days=i)).isoformat(),1+i/100])
            self.assertEqual(len(read_universe(p)),30)

if __name__ == "__main__":
    unittest.main()
