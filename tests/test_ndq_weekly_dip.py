"""Synthetic tests for weekly NDQ DCA and recurring drawdown purchases."""
import unittest
from datetime import date, timedelta
from scripts.ndq_weekly_dip import simulate_weekly

CONFIG = {"brokerage": 0, "slippage": 0}


def sample_prices():
    day = date(2024, 1, 1)
    rows = {}
    while len(rows) < 55:
        if day.weekday() < 5:
            # After 30 sessions, price falls by 10% and stays there.
            px = 10.0 if len(rows) < 30 else 9.0
            rows[day.isoformat()] = {"open": px, "close": px, "split": 1}
        day += timedelta(days=1)
    return rows


class WeeklyDipTests(unittest.TestCase):
    def test_baseline_has_no_extra_deposits(self):
        p = sample_prices()
        r = simulate_weekly(p, [], min(p), max(p), CONFIG, False)
        self.assertEqual(r["dip_weeks"], 0)
        self.assertEqual(r["extra_contributions"], 0)
        self.assertEqual(r["contributions"], 11 * 500)

    def test_dip_adds_100_every_eligible_week(self):
        p = sample_prices()
        r = simulate_weekly(p, [], min(p), max(p), CONFIG, True)
        self.assertGreaterEqual(r["dip_weeks"], 2)
        self.assertEqual(r["extra_contributions"], 100 * r["dip_weeks"])
        self.assertEqual(r["contributions"], 5500 + r["extra_contributions"])

    def test_dip_uses_prior_close_not_purchase_day_close(self):
        p = sample_prices()
        # Monday of week 7 is first session after 30 normal closes;
        # its opening trade cannot react to its own closing price.
        r = simulate_weekly(p, [], min(p), max(p), CONFIG, True)
        self.assertEqual(r["dip_weeks"], 4)

    def test_stricter_thresholds_trigger_no_more_often(self):
        p = sample_prices()
        results = [simulate_weekly(p, [], min(p), max(p), CONFIG, True, threshold)
                   for threshold in (0.05, 0.10, 0.15)]
        self.assertGreaterEqual(results[0]['dip_weeks'], results[1]['dip_weeks'])
        self.assertGreaterEqual(results[1]['dip_weeks'], results[2]['dip_weeks'])
        self.assertEqual(results[2]['dip_weeks'], 0)
        self.assertEqual(results[1]['dip_threshold'], 0.10)

    def test_no_initial_lump_sum(self):
        p = sample_prices()
        r = simulate_weekly(p, [], min(p), max(p), CONFIG, False)
        self.assertEqual(r["contributions"], 5500)


if __name__ == "__main__":
    unittest.main()
