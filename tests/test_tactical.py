"""Synthetic tests for peak-based re-entry and causal monthly trend signals."""
import unittest
from datetime import date,timedelta
from etf_backtest.engine import simulate
from etf_backtest.trend import build_signals

BASE=dict(initial_capital=1000,monthly_contribution=100,brokerage=0,slippage=0)


def fixture(rows):
    return {'X':{d:dict(open=o,close=c,split=s) for d,o,c,s in rows}}


class TacticalTests(unittest.TestCase):
    def test_peak_can_trigger_above_original_exit(self):
        rows=[('2020-01-02',10,12,1),('2020-01-03',12,16,1),
              ('2020-01-06',14,13.6,1),('2020-01-07',14,14,1)]
        p=fixture(rows)
        peak,path,ledger=simulate(p,{'X':[]},{'X':1},rows[0][0],rows[-1][0],BASE,.2,0,.15,'peak')
        fixed,_,_=simulate(p,{'X':[]},{'X':1},rows[0][0],rows[-1][0],BASE,.2,0,.15)
        self.assertEqual(peak['completed_reentries'],1)
        self.assertEqual(fixed['completed_reentries'],0)
        self.assertEqual(path[2]['reference_peak'],1600)
        self.assertEqual([e['price'] for e in ledger if e['event']=='buy'],[10,14])

    def test_peak_uses_closes_not_intraday_or_exit_open(self):
        rows=[('2020-01-02',10,12,1),('2020-01-03',12,10,1),('2020-01-06',20,9,1)]
        r,path,_=simulate(fixture(rows),{'X':[]},{'X':1},rows[0][0],rows[-1][0],BASE,.2,0,.15,'peak')
        self.assertEqual(r['pending_reentry'],0)
        self.assertEqual(path[-1]['reference_peak'],1000)

    def test_trend_uses_prior_signal_at_initial_open(self):
        rows=[('2020-02-03',10,10,1),('2020-02-04',10,10,1)]
        r,_,ledger=simulate(fixture(rows),{'X':[]},{'X':1},rows[0][0],rows[-1][0],BASE,
                            trend_signals={'2020-01-31':True})
        self.assertEqual(r['completed_entries'],1)
        self.assertEqual([e['date'] for e in ledger if e['event']=='buy'],['2020-02-03'])

    def test_month_end_signal_cannot_buy_same_open(self):
        rows=[('2020-01-30',10,10,1),('2020-01-31',10,20,1),('2020-02-03',12,12,1)]
        r,_,ledger=simulate(fixture(rows),{'X':[]},{'X':1},rows[0][0],rows[-1][0],BASE,
                            trend_signals={'2020-01-31':True})
        self.assertEqual(r['completed_entries'],1)
        self.assertEqual([e['price'] for e in ledger if e['event']=='buy'],[12])
        self.assertEqual([e['date'] for e in ledger if e['event']=='buy'],['2020-02-03'])
        self.assertEqual(r['contributed_capital'],1100)

    def test_trend_exits_and_reenters_after_confirmed_signals(self):
        rows=[('2020-01-02',10,10,1),('2020-01-31',10,8,1),('2020-02-03',7,7,1),
              ('2020-02-28',8,9,1),('2020-03-02',10,10,1)]
        signals={'2019-12-31':True,'2020-01-31':False,'2020-02-28':True}
        r,_,ledger=simulate(fixture(rows),{'X':[]},{'X':1},rows[0][0],rows[-1][0],BASE,trend_signals=signals)
        self.assertEqual(r['completed_exits'],1)
        self.assertEqual(r['completed_reentries'],1)
        self.assertEqual([e['date'] for e in ledger if e['event']=='sell'],['2020-02-03'])
        self.assertEqual([e['date'] for e in ledger if e['event']=='reentry_fill'],['2020-03-02'])

    def test_final_trend_entry_stays_pending(self):
        rows=[('2020-01-30',10,10,1),('2020-01-31',10,11,1)]
        r,_,_=simulate(fixture(rows),{'X':[]},{'X':1},rows[0][0],rows[-1][0],BASE,trend_signals={'2020-01-31':True})
        self.assertEqual(r['completed_entries'],0)
        self.assertEqual(r['pending_initial_entry'],1)
        self.assertEqual(r['pending_reentry'],0)
        self.assertEqual(r['final_cash'],1000)

    def test_signal_history_no_future_leakage_and_full_warmup(self):
        start=date(2020,1,1);p={'X':{}}
        for i in range(415):
            d=start+timedelta(days=i)
            if d.weekday()<5:
                v=10+i/100;p['X'][d.isoformat()]=dict(open=v,close=v,split=1)
        signals,history,ready=build_signals(p,{'X':[]},{'X':1},10)
        self.assertEqual(min(signals),'2020-11-30')
        self.assertEqual(ready,'2020-12-01')
        changed={'X':{d:dict(q) for d,q in p['X'].items()}}
        for d,q in changed['X'].items():
            if d>'2020-12-31':q['close']*=20
        later,_,_=build_signals(changed,{'X':[]},{'X':1},10)
        self.assertEqual({d:v for d,v in signals.items() if d<='2020-12-31'},
                         {d:v for d,v in later.items() if d<='2020-12-31'})
        # January 2021 is complete; February's partial month cannot signal.
        self.assertNotIn('2021-02-26',signals)

    def test_distribution_and_split_do_not_fake_trend_losses(self):
        p={'X':{'2020-01-02':dict(open=10,close=10,split=1),
                '2020-02-28':dict(open=5,close=5,split=2),
                '2020-03-31':dict(open=4,close=4,split=1),
                '2020-04-30':dict(open=4,close=4,split=1)}}
        divs={'X':[dict(ex_date='2020-03-31',pay_date='2020-04-01',amount=1)]}
        signals,history,_=build_signals(p,divs,{'X':1},2)
        self.assertEqual([r['total_return_index'] for r in history],[100,100,100])
        self.assertFalse(signals['2020-03-31'])  # equality selects cash

    def test_signal_portfolio_rebalances_monthly(self):
        p={s:{} for s in ('A','B')}
        for d,a,b in [('2020-01-02',10,10),('2020-02-28',20,10),('2020-03-31',10,20)]:
            for s,v in [('A',a),('B',b)]:p[s][d]=dict(open=v,close=v,split=1)
        _,history,_=build_signals(p,{'A':[],'B':[]},{'A':.5,'B':.5},2)
        self.assertEqual([r['total_return_index'] for r in history],[150,187.5])

    def test_peak_reference_includes_distributions(self):
        rows=[('2020-01-02',10,12,1),('2020-01-03',12,16,1),('2020-01-06',13,13,1)]
        div={'X':[dict(ex_date='2020-01-06',pay_date='2020-01-07',amount=3)]}
        r,path,_=simulate(fixture(rows),div,{'X':1},rows[0][0],rows[-1][0],BASE,.2,0,.15,'peak')
        self.assertEqual(path[-1]['reference_value'],1600)
        self.assertEqual(r['pending_reentry'],0)
        self.assertEqual(r['final_cash'],1200)

    def test_missing_month_end_resets_consecutive_history(self):
        p={s:{} for s in ('A','B')}
        for d in ['2020-01-02','2020-02-27','2020-02-28','2020-03-31','2020-04-30','2020-05-29']:
            p['A'][d]=dict(open=10,close=10,split=1)
            if d!='2020-02-28':p['B'][d]=dict(open=10,close=10,split=1)
        signals,h,ready=build_signals(p,{'A':[],'B':[]},{'A':.5,'B':.5},2)
        self.assertNotIn('2020-02-27',signals)
        self.assertNotIn('2020-03-31',signals)
        self.assertEqual(min(signals),'2020-04-30')
        self.assertEqual(h[0]['date'],'2020-02-28')
        self.assertEqual(h[0]['total_return_index'],'')
        single,_,_=build_signals(p,{'A':[],'B':[]},{'B':1},2)
        self.assertEqual(min(single),'2020-04-30')

if __name__=='__main__':unittest.main()
