"""Small synthetic fixtures only; never used as investment-history results."""
import unittest
from datetime import date
from etf_backtest.engine import simulate, xirr

BASE=dict(initial_capital=1000,monthly_contribution=100,brokerage=0,slippage=0)


def prices(rows):
    return {'X':{d:dict(open=o,close=c,split=split) for d,o,c,split in rows}}


def run(rows,divs=(),threshold=None,**settings):
    p=prices(rows)
    return simulate(p,{'X':list(divs)},{'X':1},rows[0][0],rows[-1][0],{**BASE,**settings},threshold)


class AccountingTests(unittest.TestCase):
    def test_contributions_not_profit(self):
        r,path,_=run([('2020-01-02',10,10,1),('2020-02-03',10,10,1),('2020-03-02',10,10,1)])
        self.assertEqual(r['contributed_capital'],1200)
        self.assertEqual(r['profit'],0)
        self.assertEqual(r['maximum_drawdown'],0)

    def test_contributions_dilute_target(self):
        r,_,_=run([('2020-01-02',10,10,1),('2020-02-03',11.5,11.5,1)],threshold=.15)
        self.assertEqual(r['never_reached_target'],1)
        self.assertAlmostEqual(r['profit'],150)

    def test_threshold_and_next_open_gap(self):
        r,_,ledger=run([('2020-01-02',10,11.5,1),('2020-01-03',9,9,1)],threshold=.15)
        self.assertEqual(r['signal_date'],'2020-01-02')
        self.assertEqual(r['exit_date'],'2020-01-03')
        self.assertEqual(r['final_wealth'],900)
        self.assertEqual([e['price'] for e in ledger if e['event']=='sell'],[9])

    def test_final_signal_is_pending(self):
        r,_,_=run([('2020-01-02',10,12,1)],threshold=.20)
        self.assertEqual(r['pending_exit'],1)
        self.assertEqual(r['completed_exits'],0)
        self.assertEqual(r['never_reached_target'],0)

    def test_no_intraday_high_signal(self):
        r,_,_=run([('2020-01-02',12,10,1),('2020-01-03',12,10,1)],threshold=.15)
        self.assertEqual(r['never_reached_target'],1)

    def test_cash_and_contributions_after_exit(self):
        r,_,ledger=run([('2020-01-02',10,12,1),('2020-01-03',12,12,1),('2020-02-03',20,20,1)],threshold=.15)
        self.assertEqual(r['final_cash'],1300)
        self.assertEqual(r['contributed_capital'],1100)
        self.assertEqual(len([e for e in ledger if e['event']=='buy']),1)

    def test_ex_date_price_drop_not_double_counted(self):
        div=dict(ex_date='2020-01-03',pay_date='2020-01-06',amount=1)
        r,path,_=run([('2020-01-02',10,10,1),('2020-01-03',9,9,1),('2020-01-06',9,9,1)],[div])
        self.assertEqual(r['final_wealth'],1000)
        self.assertEqual(path[1]['receivables'],100)
        self.assertEqual(path[1]['cash'],0)
        self.assertEqual(path[2]['cash'],100)
        self.assertEqual(r['distribution_entitlements'],100)

    def test_new_ex_date_buyer_not_entitled(self):
        div=dict(ex_date='2020-01-02',pay_date='2020-01-03',amount=1)
        r,_,_=run([('2020-01-02',10,10,1),('2020-01-03',10,10,1)],[div])
        self.assertEqual(r['distribution_entitlements'],0)

    def test_same_day_payment_is_recorded_once(self):
        div=dict(ex_date='2020-01-03',pay_date='2020-01-03',amount=1)
        r,_,ledger=run([('2020-01-02',10,10,1),('2020-01-03',9,9,1)],[div])
        self.assertEqual(r['final_wealth'],1000)
        self.assertEqual(sum(e['amount'] for e in ledger if e['event']=='distribution_payment'),100)

    def test_sell_ex_date_keeps_receivable(self):
        div=dict(ex_date='2020-01-03',pay_date='2020-01-06',amount=1)
        r,_,_=run([('2020-01-02',10,12,1),('2020-01-03',11,11,1),('2020-01-06',11,11,1)],[div],threshold=.15)
        self.assertEqual(r['final_cash'],1200)

    def test_split_preserves_wealth(self):
        r,_,_=run([('2020-01-02',10,10,1),('2020-01-03',5,5,2)])
        self.assertEqual(r['final_wealth'],1000)

    def test_costs_and_whole_units(self):
        r,_,_=run([('2020-01-02',10,10,1)],brokerage=5,slippage=.01)
        # 98 units at 10.1 + 5; then terminal 9.9*98 - 5 and residual cash.
        self.assertAlmostEqual(r['final_wealth'],970.4)
        self.assertEqual(r['brokerage_paid'],5)

    def test_drawdown_adjusts_contributions(self):
        r,_,_=run([('2020-01-02',10,10,1),('2020-02-03',10,5,1)])
        self.assertAlmostEqual(r['maximum_drawdown'],-.5)

    def test_xirr(self):
        r=xirr([(date(2020,1,1),-1000),(date(2021,1,1),1100)])
        self.assertAlmostEqual((1+r)**(366/365.25),1.1)

    def test_cash_interest_on_actual_days(self):
        p=prices([('2020-01-02',10,12,1),('2020-01-03',12,12,1),('2020-01-06',12,12,1)])
        r,_,_=simulate(p,{'X':[]},{'X':1},'2020-01-02','2020-01-06',BASE,.15,.03)
        self.assertAlmostEqual(r['final_wealth'],1200*1.03**(3/365.25))

    def test_calendar_mismatch_fails(self):
        p=prices([('2020-01-02',10,10,1)]);p['Y']={}
        with self.assertRaises(ValueError):simulate(p,{'X':[],'Y':[]},{'X':.5,'Y':.5},'2020-01-02','2020-01-03',BASE)

if __name__=='__main__':unittest.main()
