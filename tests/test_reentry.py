"""Synthetic re-entry fixtures, separate from actual historical results."""
import unittest
from etf_backtest.engine import simulate

BASE=dict(initial_capital=1000,monthly_contribution=100,brokerage=0,slippage=0)


def run(rows,divs=(),**settings):
    p={'X':{d:dict(open=o,close=c,split=s) for d,o,c,s in rows}}
    return simulate(p,{'X':list(divs)},{'X':1},rows[0][0],rows[-1][0],{**BASE,**settings},.20,0,.15)


class ReentryTests(unittest.TestCase):
    def test_two_cycles_reset_and_next_open(self):
        rows=[('2020-01-02',10,12,1),('2020-01-03',12,12,1),
              ('2020-01-06',10.2,10.2,1),('2020-01-07',9,9,1),
              ('2020-01-08',9,11,1),('2020-01-09',11,11,1),
              ('2020-01-10',9.35,9.35,1),('2020-01-13',8,8,1)]
        r,path,ledger=run(rows)
        self.assertEqual(r['completed_exits'],2)
        self.assertEqual(r['completed_reentries'],2)
        self.assertEqual(r['pending_exit'],0)
        self.assertEqual(r['final_wealth'],1466)
        self.assertEqual(path[-1]['cycle_gain'],0)
        self.assertEqual([e['date'] for e in ledger if e['event']=='reentry_signal'],['2020-01-06','2020-01-10'])
        self.assertEqual([e['date'] for e in ledger if e['event']=='reentry_fill'],['2020-01-07','2020-01-13'])
        self.assertEqual([e['price'] for e in ledger if e['event']=='buy'],[10,9,8])

    def test_reference_is_exit_not_later_peak(self):
        r,_,_=run([('2020-01-02',10,12,1),('2020-01-03',12,20,1),('2020-01-06',16,16,1)])
        # 20% below the later peak, but still ABOVE the actual exit price.
        self.assertEqual(r['completed_reentries'],0)
        self.assertEqual(r['pending_reentry'],0)
        self.assertEqual(r['waiting_for_reentry'],1)

    def test_cash_contributions_do_not_change_trigger(self):
        r,path,_=run([('2020-01-02',10,12,1),('2020-01-03',12,12,1),('2020-02-03',11,11,1)])
        self.assertEqual(r['contributed_capital'],1100)
        self.assertEqual(r['final_cash'],1300)
        self.assertEqual(r['pending_reentry'],0)
        self.assertEqual(path[-1]['exit_reference'],1200)

    def test_new_cycle_includes_accumulated_contributions(self):
        r,path,_=run([('2020-01-02',10,12,1),('2020-01-03',12,12,1),
                     ('2020-02-03',10.2,10.2,1),('2020-02-04',10,10,1)])
        self.assertEqual(r['completed_reentries'],1)
        self.assertEqual(path[-1]['cycle_capital'],1300)
        self.assertEqual(path[-1]['cycle_gain'],0)

    def test_distributions_not_a_false_drop_or_real_income_while_out(self):
        div=dict(ex_date='2020-01-06',pay_date='2020-01-07',amount=2)
        r,path,_=run([('2020-01-02',10,12,1),('2020-01-03',12,12,1),
                      ('2020-01-06',10,10,1),('2020-01-07',10,10,1)],[div])
        self.assertEqual(r['pending_reentry'],0)
        self.assertEqual(r['completed_reentries'],0)
        self.assertEqual(path[-1]['reference_value'],1200)
        self.assertEqual(r['final_cash'],1200)
        self.assertEqual(r['distribution_entitlements'],0)

    def test_reference_adjusts_splits(self):
        r,path,_=run([('2020-01-02',10,12,1),('2020-01-03',12,12,1),('2020-01-06',6,6,2)])
        self.assertEqual(r['pending_reentry'],0)
        self.assertEqual(path[-1]['reference_value'],1200)

    def test_final_reentry_signal_is_pending(self):
        r,_,_=run([('2020-01-02',10,12,1),('2020-01-03',12,12,1),('2020-01-06',10.2,10.2,1)])
        self.assertEqual(r['pending_reentry'],1)
        self.assertEqual(r['completed_reentries'],0)

    def test_overnight_rebound_fills_without_lookahead_cancellation(self):
        r,_,ledger=run([('2020-01-02',10,12,1),('2020-01-03',12,12,1),
                      ('2020-01-06',10.2,10.2,1),('2020-01-07',13,13,1)])
        self.assertEqual(r['completed_reentries'],1)
        self.assertEqual([e['price'] for e in ledger if e['event']=='buy'],[10,13])

    def test_real_distribution_receivable_survives_exit(self):
        div=dict(ex_date='2020-01-03',pay_date='2020-02-05',amount=1)
        r,path,_=run([('2020-01-02',10,12,1),('2020-01-03',11,11,1),
                     ('2020-01-06',9.35,9.35,1),('2020-01-07',9,9,1)],[div])
        self.assertEqual(r['final_receivables'],100)
        self.assertEqual(path[-1]['cycle_capital'],1200)
        self.assertEqual(r['completed_reentries'],1)

    def test_multi_etf_reference_tracks_exact_sold_units(self):
        days=['2020-01-02','2020-01-03','2020-01-06','2020-01-07']
        p={'A':{},'B':{}}
        for d,o,c in zip(days,[10,12,10.2,10],[12,12,10.2,10]):
            p['A'][d]=dict(open=o,close=c,split=1)
            p['B'][d]=dict(open=2*o,close=2*c,split=1)
        r,path,_=simulate(p,{'A':[],'B':[]},{'A':.5,'B':.5},days[0],days[-1],BASE,.20,0,.15)
        self.assertEqual(path[2]['exit_reference'],1200)
        self.assertAlmostEqual(path[2]['reference_value'],1020)
        self.assertEqual(r['completed_reentries'],1)
        self.assertEqual(r['final_wealth'],1200)

    def test_costs_are_charged_again_on_reentry(self):
        r,_,_=run([('2020-01-02',10,13,1),('2020-01-03',13,13,1),
                   ('2020-01-06',11.05,11.05,1),('2020-01-07',10,10,1)],brokerage=5,slippage=.01)
        self.assertEqual(r['completed_reentries'],1)
        self.assertEqual(r['brokerage_paid'],15)
        self.assertAlmostEqual(r['final_wealth'],1226.66)

if __name__=='__main__':unittest.main()
