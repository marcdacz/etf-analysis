import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from etf_backtest.data import normalise


class DataTests(unittest.TestCase):
    def test_split_adjustment_and_cash_only_distribution(self):
        # Yahoo historical quote 5 before a later 2:1 split represents a
        # contemporaneous price of 10. Adjusted close must never be used.
        chart={'chart':{'result':[{'meta':{'currency':'AUD'},'timestamp':[1577923200,1578009600],
            'events':{'splits':{'a':{'date':1578009600,'numerator':2,'denominator':1}}},
            'indicators':{'quote':[{'open':[5,5],'close':[5,5],'high':[5,5],'low':[5,5],'volume':[100,100]}],
                          'adjclose':[{'adjclose':[3,3]}]}}]}}
        issuer={'data':{'items':[{'exDividendDate':'2020-01-03','payableDate':'2020-01-06','taxDetails':[
            {'distributionType':{'distCode':'CASH'},'distributionAmount':1},
            {'distributionType':{'distCode':'GRSS'},'distributionAmount':2}]}]}}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'data/raw';raw.mkdir(parents=True)
            (raw/'VAS-prices.json').write_text(json.dumps(chart))
            (raw/'VAS-distributions.json').write_text(json.dumps(issuer))
            with patch('etf_backtest.data.FUNDS',{'VAS':'8205'}):normalise(root)
            import csv
            with open(root/'data/normalized/VAS-prices.csv') as f:p=list(csv.DictReader(f))
            with open(root/'data/normalized/VAS-distributions.csv') as f:d=list(csv.DictReader(f))
            self.assertEqual(float(p[0]['close']),10)
            self.assertEqual(float(p[1]['close']),5)
            self.assertEqual(float(p[1]['split']),2)
            self.assertEqual(float(d[0]['amount']),1)

if __name__=='__main__':unittest.main()
