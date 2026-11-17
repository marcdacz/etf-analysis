"""Repeated 20% gain exits and 15% below-exit re-entry, using actual history."""
from collections import defaultdict
from datetime import date
import hashlib
import json
import statistics
from .analysis import chart, make_windows, pct, prepare_data, validate_config
from .data import write_csv
from .engine import simulate


def check_case(result, ledger, target, drop):
    cash=sum(e['amount'] for e in ledger if e['event'] in ('contribution','buy','sell','distribution_payment'))+result['cash_interest']
    assert abs(cash-result['final_cash'])<1e-5, 'Cash reconciliation failed'
    assert abs(sum(e['amount'] for e in ledger if e['event']=='contribution')-result['contributed_capital'])<1e-6
    assert abs(sum(e['amount'] for e in ledger if e['event']=='distribution_entitlement')-result['distribution_entitlements'])<1e-6
    exit_signal=None;entry_signal=None;exits=0;entries=0
    for event in ledger:
        if event['event']=='exit_signal':
            assert event['amount']+1e-10>=target
            exit_signal=event['date']
        elif event['event']=='exit_fill':
            assert exit_signal and exit_signal<event['date']
            exits+=1;exit_signal=None
        elif event['event']=='reentry_signal':
            assert event['amount']<=-drop+1e-10
            entry_signal=event['date']
        elif event['event']=='reentry_fill':
            assert entry_signal and entry_signal<event['date']
            entries+=1;entry_signal=None
    if drop is not None:
        assert exits==result['completed_exits']
        assert entries==result['completed_reentries']
        assert entries<=exits<=entries+1
        assert bool(exit_signal)==bool(result['pending_exit'])
        assert bool(entry_signal)==bool(result['pending_reentry'])


def cycles_from_ledger(metadata, ledger, finish):
    cycles=[];current=None
    for e in ledger:
        kind=e['event']
        if kind=='cycle_start':
            current=dict(**metadata,cycle=len(cycles)+1,entry_date=e['date'],capital_at_entry=e['amount'],
                exit_signal_date='',exit_date='',exit_wealth='',reference_at_exit='',reentry_signal_date='',reentry_date='',wait_days=0,end_status='invested')
            cycles.append(current)
        elif current is not None:
            if kind=='exit_signal':current.update(exit_signal_date=e['date'],end_status='pending_exit')
            elif kind=='exit_reference':current['reference_at_exit']=e['amount']
            elif kind=='exit_fill':current.update(exit_date=e['date'],exit_wealth=e['amount'],end_status='waiting')
            elif kind=='reentry_signal':current.update(reentry_signal_date=e['date'],end_status='pending_reentry')
            elif kind=='reentry_fill':current.update(reentry_date=e['date'],end_status='reentered')
    for c in cycles:
        if c['exit_date']:
            c['wait_days']=(date.fromisoformat(c['reentry_date'] or finish)-date.fromisoformat(c['exit_date'])).days
    return cycles


def run(root, config, rules):
    validate_config(config)
    target=rules['exit_threshold'];drop=rules['reentry_drop']
    if not 0<target or not 0<drop<1:raise ValueError('Invalid re-entry thresholds')
    if rules['reference']!='exit_fixed_basket_total_return' or rules['target_reset']!='cycle_capital':
        raise ValueError('Unsupported reference or reset convention')
    prices,distributions,audit,gaps,common=prepare_data(root,config)
    out=root/'results/reentry';out.mkdir(parents=True,exist_ok=True)
    defaults=dict(completed_reentries=0,pending_reentry=0,waiting_for_reentry=0,cash_days=0,
                  last_exit_date='',last_entry_date='',waiting_days=0)
    rows=[];ledgers=[];cycles=[];daily=[];paths={};checks=0
    cash_name=f'exit_{target*100:g}_cash'
    reentry_name=f'exit_{target*100:g}_reenter_{drop*100:g}'
    strategies=[('hold',None,None),(cash_name,target,None),(reentry_name,target,drop)]
    studies=[('main',config['portfolios'],config['initial_capital']),
             ('supplemental',config['supplemental']['portfolios'],config['supplemental']['initial_capital'])]
    for study,portfolios,capital in studies:
        settings={**config,'initial_capital':capital}
        for name,weights in portfolios.items():
            windows=make_windows(prices,weights,config,common)
            print(f'Re-entry study: {study}: {name}: {len(windows)} windows',flush=True)
            for window,begin,finish in sorted(windows):
                for rate in config['cash_rates']:
                    baseline=None
                    for strategy,threshold,reenter in strategies:
                        result,path,ledger=simulate(prices,distributions,weights,begin,finish,settings,threshold,rate,reenter)
                        check_case(result,ledger,threshold,reenter);checks+=1
                        if strategy=='hold':baseline=result
                        assert result['contributed_capital']==baseline['contributed_capital']
                        if reenter is None:
                            result.update(last_entry_date=result['start'],last_exit_date=result['exit_date'])
                            if result['exit_date']:
                                result['cash_days']=(date.fromisoformat(result['end'])-date.fromisoformat(result['exit_date'])).days
                        metadata=dict(study=study,portfolio=name,window=window,cash_rate=rate,strategy=strategy)
                        row=dict(**metadata,**{**defaults,**result},
                            wealth_minus_hold=result['final_wealth']-baseline['final_wealth'],
                            data_gap_affected=int(any(result['start']<=g<=result['end'] for g in gaps)),history_type='actual ETF')
                        rows.append(row)
                        if window in ('full','common') or (reenter is not None and result['completed_reentries']):
                            detail_metadata=dict(**metadata,trial_start=result['start'],trial_end=result['end'])
                            ledgers.extend(dict(**detail_metadata,**event) for event in ledger)
                            if reenter is not None:cycles.extend(cycles_from_ledger(detail_metadata,ledger,result['end']))
                        if study=='main' and window=='common' and rate==0:
                            paths[(name,strategy)]=path
                            for p in path:
                                point=dict(cycle_capital='',cycle_gain='',state='invested',reference_value='',exit_reference='',**{k:v for k,v in p.items() if k not in ('cycle_capital','cycle_gain','state','reference_value','exit_reference')})
                                point.update({k:v for k,v in p.items() if k in ('cycle_capital','cycle_gain','state','reference_value','exit_reference')})
                                if reenter is None and result['exit_date'] and p['date']>=result['exit_date']:point['state']='cash'
                                daily.append(dict(portfolio=name,strategy=strategy,**point))
    paired={(r['study'],r['portfolio'],r['window'],r['start'],r['end'],r['cash_rate']):r for r in rows if r['strategy']==cash_name}
    for r in rows:
        b=paired[(r['study'],r['portfolio'],r['window'],r['start'],r['end'],r['cash_rate'])]
        r['wealth_minus_exit_cash']=r['final_wealth']-b['final_wealth']
    write_csv(out/'trials.csv',rows);write_csv(out/'trade_ledger.csv',ledgers)
    write_csv(out/'cycles.csv',cycles);write_csv(out/'common_daily.csv',daily)
    groups=defaultdict(list)
    for r in rows:
        if not r['window'].endswith('m'):continue
        cohorts=['all_available']+(['common_entries'] if r['start']>=common else [])
        for cohort in cohorts:
            groups[(r['study'],cohort,r['portfolio'],r['window'],r['cash_rate'],r['strategy'],r['data_gap_affected'])].append(r)
    summary=[]
    for key,group in sorted(groups.items()):
        study,cohort,name,window,rate,strategy,gap=key
        summary.append(dict(study=study,cohort=cohort,portfolio=name,window=window,cash_rate=rate,strategy=strategy,data_gap_affected=gap,
            trials=len(group),trials_with_reentry=sum(r['completed_reentries']>0 for r in group),
            completed_exits=sum(r['completed_exits'] for r in group),completed_reentries=sum(r['completed_reentries'] for r in group),
            never_reached_target=sum(r['never_reached_target'] for r in group),
            waiting_for_reentry=sum(r['waiting_for_reentry'] for r in group),
            pending_reentry=sum(r['pending_reentry'] for r in group),pending_exit=sum(r['pending_exit'] for r in group),
            median_final_wealth=statistics.median(r['final_wealth'] for r in group),
            median_mwr=statistics.median(r['money_weighted_return'] for r in group),
            median_wealth_minus_hold=statistics.median(r['wealth_minus_hold'] for r in group),
            median_wealth_minus_exit_cash=statistics.median(r['wealth_minus_exit_cash'] for r in group),
            beat_hold=sum(r['wealth_minus_hold']>1e-6 for r in group),
            beat_exit_cash=sum(r['wealth_minus_exit_cash']>1e-6 for r in group),
            worst_drawdown=min(r['maximum_drawdown'] for r in group),median_cash_days=statistics.median(r['cash_days'] for r in group)))
    write_csv(out/'summary.csv',summary)
    for i,name in enumerate(config['portfolios']):
        series=[]
        for strategy,_,_ in strategies:
            p=paths[(name,strategy)];origin=date.fromisoformat(p[0]['date'])
            series.append((strategy,[((date.fromisoformat(v['date'])-origin).days,v['wealth']) for v in p]))
        chart(out/f'wealth_{i+1}.svg',f'{name}: exit {target:.0%}, re-enter after {drop:.0%} fall',series,
              f'AUD, {common} to {config["end"]}; 0% cash; data gaps flagged')
    write_report(out,rows,summary,common,gaps,config,rules)
    files=[root/'config.json',root/'config_reentry.json',*sorted((root/'data/raw').glob('*')),
           *sorted((root/'data/normalized').glob('*')),*sorted((root/'etf_backtest').glob('*.py')),
           *sorted((root/'tests').glob('*.py'))]
    inputs={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
    outputs={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.suffix in ('.csv','.svg') or p.name=='report.md'}
    (out/'run_manifest.json').write_text(json.dumps(dict(configuration=config,rules=rules,sha256=inputs,output_sha256=outputs,trial_count=len(rows)),indent=2)+'\n')
    (out/'validation.json').write_text(json.dumps(dict(status='passed; source gaps remain disclosed',trials_reconciled=checks,
        checks=['all trial cash and contribution reconciliation','real distribution entitlement reconciliation','all re-entry and exit fill markers strictly after signals',
                '20% cycle gain and 15% reference drawdown thresholds','paired contributions identical','re-entry counts do not exceed exits'],
        excluded_dates=gaps),indent=2)+'\n')
    print(f'Wrote {len(rows)} reconciled scenarios to {out}',flush=True)


def write_report(out,rows,summary,common,gaps,config,rules):
    commonrows=[r for r in rows if r['study']=='main' and r['window']=='common' and r['cash_rate']==0]
    lines=['# Exit at 20%, re-enter after a 15% fall — pre-tax backtest','',
        f'Actual cached ETF history through {config["end"]}. Same five portfolios, A${config["initial_capital"]:,.0f} initially and A${config["monthly_contribution"]:,.0f} monthly from the following month. The A$10,000 supplemental study is retained in the CSVs. No new price downloads or proxy histories.','',
        '## Exact rules','',
        '1. Start invested. Exit when net liquidation wealth is at least 20% above the current cycle’s contributed capital. Contributions while invested increase both wealth and the target capital; they are not profit.',
        '2. Sell at the next available open after a closing signal. The re-entry reference is the exact units sold, valued at the exit-day opening market prices before brokerage/slippage. It excludes unrelated cash and unpaid distributions already earned before selling.',
        '3. While waiting, track those same hypothetical units, adjust for splits, and add cash distributions earned after the exit to the reference basket on their ex-dates, without reinvestment. Re-enter when this basket closes at or below 85% of its fixed exit reference. This is a fall from the exit, NOT a fall from a subsequent high. Reference distributions are hypothetical: they are never credited to the real cash account.',
        '4. Re-enter at the following available open even if prices rebound overnight. Invest all affordable cash in whole units at the original target allocations, including contributions and cash interest accumulated while waiting. A$5 brokerage per ETF order and 5bp adverse slippage apply to every purchase and sale.',
        '5. Reset cycle capital to account wealth just before re-entry purchases (cash plus any real distribution receivables). Retained earlier profits are part of this new capital. Future contributions while invested increase it. Repeat the 20% exit/15% re-entry rule; no stop-loss.',
        '6. Continue identical monthly contributions in every strategy. Uninvested cash earns either 0% or a hypothetical constant 3% annually. Actual distributions follow issuer payment dates and reinvest only at scheduled monthly purchases. Final-day signals remain pending; terminal wealth includes estimated liquidation costs.','',
        f'Example ignoring contributions, distributions and costs: buy at 100, sell at {100*(1+rules["exit_threshold"]):.2f}; re-entry is triggered at {100*(1+rules["exit_threshold"])*(1-rules["reentry_drop"]):.2f} or below and executes at the next open. The next target becomes {1+rules["exit_threshold"]:.2f} times the reinvested capital.','',
        '**Data qualification:** missing sessions '+', '.join(gaps)+' are omitted without imputation. All crossed windows are flagged; signals, trade timing and drawdowns can be affected. Current common-period results are qualified estimates. No future-performance guarantee.','',
        '## Common-period results','',
        f'{common}–{config["end"]}, 0% cash interest. All strategies receive identical contributions. MWR is annualised XIRR; drawdown is adjusted for contributions. Cash days are calendar days fully out of ETF holdings after exits; residual cash while invested is excluded.','',
        '| Portfolio | Strategy | Final wealth | Contributed | Profit | MWR/year | Max drawdown | Exits | Re-entries | Cash days | Still waiting |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in commonrows:
        lines.append(f'| {r["portfolio"]} | {r["strategy"]} | {r["final_wealth"]:,.0f} | {r["contributed_capital"]:,.0f} | {r["profit"]:,.0f} | {pct(r["money_weighted_return"])} | {pct(r["maximum_drawdown"])} | {r["completed_exits"]} | {r["completed_reentries"]} | {r["cash_days"]} | {bool(r["waiting_for_reentry"])} |')
    new=[r for r in commonrows if '_reenter_' in r['strategy']]
    lines+=['','## Interpretation','',
        f'The re-entry rule completed {sum(r["completed_reentries"] for r in new)} re-entries across the five common-period accounts. It beat buy-and-hold on terminal wealth in {sum(r["wealth_minus_hold"]>1e-6 for r in new)} of five comparisons, and beat exiting permanently in {sum(r["wealth_minus_exit_cash"]>1e-6 for r in new)} of five. {sum(r["waiting_for_reentry"] for r in new)} accounts were still waiting at the end. These are five selected portfolios on one shared historical path, not independent forecasts.', '',
        'A market can fall substantially from a later high without ever getting 15% below an earlier sale. That can leave the strategy in cash for years. A successful dip purchase can improve the entry price, but re-entry exposes the account to further losses; there is no downside protection while invested. Repeated trading adds brokerage, slippage and potentially taxable realised gains. The 20% threshold can be crossed and the actual next-open sale still realise less than 20%.','',
        '## Twelve- and twenty-four-month entry cohorts','',
        'Main study, common-entry dates, 0% cash. Counts are summed across overlapping hypothetical accounts, not a single trading account. Complete and gap-affected windows are separated. Ending without a 15% dip is not a data failure: it is a legitimate cash outcome.','',
        '| Portfolio | Horizon | Gap affected | Accounts | Accounts re-entered | Re-entries | Still waiting | Never hit 20% | Median wealth vs hold | Median wealth vs exit/cash |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in summary:
        if r['study']=='main' and r['cohort']=='common_entries' and r['cash_rate']==0 and '_reenter_' in r['strategy'] and r['window'] in ('12m','24m'):
            lines.append(f'| {r["portfolio"]} | {r["window"]} | {bool(r["data_gap_affected"])} | {r["trials"]} | {r["trials_with_reentry"]} | {r["completed_reentries"]} | {r["waiting_for_reentry"]} | {r["never_reached_target"]} | {r["median_wealth_minus_hold"]:,.0f} | {r["median_wealth_minus_exit_cash"]:,.0f} |')
    lines+=['','## Longer histories and cash sensitivity','',
        'Each portfolio’s full available history is also tested, but these start dates differ and their terminal wealth must not be compared directly across portfolios. The NDQ and Vanguard histories include COVID and 2022; BGBL portfolios do not. Monthly 3/6/12/24-month and quarterly 36/60-month windows plus annual starts are in `trials.csv`; only complete horizons are included.','',
        '| Portfolio | Period | Cash rate | Final wealth | MWR/year | Max drawdown | Exits | Re-entries | Waiting days at end |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        if r['study']=='main' and r['window'] in ('full','common') and '_reenter_' in r['strategy']:
            lines.append(f'| {r["portfolio"]} | {r["window"]}: {r["start"]}–{r["end"]} | {pct(r["cash_rate"])} | {r["final_wealth"]:,.0f} | {pct(r["money_weighted_return"])} | {pct(r["maximum_drawdown"])} | {r["completed_exits"]} | {r["completed_reentries"]} | {r["waiting_days"]} |')
    lines+=['','## Artifacts, validation and limitations','',
        '`trials.csv` contains all account metrics and paired wealth differences. `cycles.csv` and `trade_ledger.csv` retain full/common accounts plus every account that actually re-entered, with trial start/end dates to distinguish overlapping cohorts. `common_daily.csv` records account state, cycle capital, and hypothetical reference basket values. `summary.csv` separates `all_available` cohorts from `common_entries` cohorts; these overlap and must not be pooled. `wealth_*.svg` charts compare all three strategies; identical lines can overlap.','',
        'Runtime validation reconciles actual cash, contributions and distribution entitlement for every trial, checks paired contribution equality and verifies all recorded re-entry/exit fills follow their signals. Unit tests include repeated cycles, target resets, accumulated contributions, fixed exit anchors, splits, distributions, pending signals and overnight gaps. Input and output hashes are pinned in `run_manifest.json`.', '',
        'All results are pre-tax, nominal AUD. Fund fees remain embedded in actual prices; personal CGT, income tax, franking credits and AMIT cost-base adjustments are excluded. Brokerage, slippage, auction liquidity and cash interest are assumptions. XIRR can be extreme over short windows. Sale proceeds are treated as immediately available; re-entry could occur before real settlement, so a broker might require cash or defer the trade. There is no leverage, no borrowing, and no forced sale at the end; liquidation costs are estimated consistently. Historical provider errors and the two missing sessions limit confidence. Funds/allocations were selected retrospectively, and overlapping windows are dependent. This study does not establish an optimal rule or guarantee future returns.']
    import re
    replacements={'20%':f'{rules["exit_threshold"]:.0%}','15%':f'{rules["reentry_drop"]:.0%}','85%':f'{1-rules["reentry_drop"]:.0%}'}
    # Narrative defaults adapt when the editable rule percentages change.
    text=re.sub(r'20%|15%|85%',lambda m:replacements[m.group()], '\n'.join(lines))
    (out/'report.md').write_text(text+'\n')


def validate(root):
    """Verify pinned files and reconcile retained ledgers against generated CSVs."""
    import csv
    out=root/'results/reentry'
    manifest=json.loads((out/'run_manifest.json').read_text())
    for rel,digest in manifest['sha256'].items():
        if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=digest:raise ValueError(f'Input changed: {rel}; rerun reentry')
    for rel,digest in manifest['output_sha256'].items():
        if hashlib.sha256((out/rel).read_bytes()).hexdigest()!=digest:raise ValueError(f'Output changed: {rel}; rerun reentry')
    target=manifest['rules']['exit_threshold'];drop=manifest['rules']['reentry_drop']
    cash_name=f'exit_{target*100:g}_cash'
    reentry_name=f'exit_{target*100:g}_reenter_{drop*100:g}'
    with open(out/'trials.csv') as f:rows=list(csv.DictReader(f))
    with open(out/'trade_ledger.csv') as f:events=list(csv.DictReader(f))
    group=defaultdict(list)
    meta=('study','portfolio','window','cash_rate','strategy','trial_start','trial_end')
    for e in events:
        for k in ('amount','units','price'):e[k]=float(e[k])
        group[tuple(e[k] for k in meta)].append(e)
    def key(r):return tuple(r[k] for k in ('study','portfolio','window','start','end','cash_rate'))
    paired={key(r):r for r in rows if r['strategy']=='hold'}
    cash_paired={key(r):r for r in rows if r['strategy']==cash_name}
    with open(root/'results/trials.csv') as f:old=list(csv.DictReader(f))
    old_paired={(key(r),r['strategy']):r for r in old}
    old_manifest=json.loads((root/'results/run_manifest.json').read_text())
    comparable=old_manifest['configuration']==manifest['configuration'] and target==.20
    baselines=0;ledgers_checked=0;identical_no_entry=0
    for r in rows:
        assert float(r['contributed_capital'])==float(paired[key(r)]['contributed_capital'])
        assert abs(float(r['final_wealth'])-float(r['contributed_capital'])-float(r['profit']))<1e-6
        if r['strategy'] in ('hold',cash_name) and comparable:
            prev=old_paired[(key(r),'hold' if r['strategy']=='hold' else 'exit_20')]
            for field in ('final_wealth','contributed_capital','profit','money_weighted_return','maximum_drawdown','brokerage_paid','distribution_entitlements'):
                assert abs(float(r[field])-float(prev[field]))<1e-7,(key(r),field)
            baselines+=1
        elif r['strategy']==reentry_name and int(r['completed_reentries'])==0:
            assert abs(float(r['final_wealth'])-float(cash_paired[key(r)]['final_wealth']))<1e-6
            identical_no_entry+=1
        if r['window'] in ('full','common') or (r['strategy']==reentry_name and int(r['completed_reentries'])):
            parsed={k:(float(v) if k in ('cash_interest','final_cash','contributed_capital','distribution_entitlements') else v) for k,v in r.items()}
            for k in ('completed_exits','completed_reentries','pending_exit','pending_reentry'):parsed[k]=int(parsed[k])
            is_reentry='_reenter_' in r['strategy']
            group_key=tuple(r[k] for k in meta[:5])+(r['start'],r['end'])
            check_case(parsed,group[group_key],None if r['strategy']=='hold' else manifest['rules']['exit_threshold'],manifest['rules']['reentry_drop'] if is_reentry else None)
            ledgers_checked+=1
    result=dict(status='passed; data gaps remain disclosed',trials_checked=len(rows),
        baseline_results_matching_original=baselines,retained_ledgers_reconciled=ledgers_checked,
        no_reentry_results_equal_permanent_exit=identical_no_entry,input_hashes_verified=len(manifest['sha256']),output_hashes_verified=len(manifest['output_sha256']))
    (out/'independent_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
