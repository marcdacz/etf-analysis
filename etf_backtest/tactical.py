"""Compare monthly trend allocation and peak-based re-entry against prior rules."""
from collections import defaultdict
from datetime import date
import csv
import hashlib
import json
import statistics
from .analysis import chart, make_windows, pct, prepare_data, validate_config
from .data import write_csv
from .engine import simulate
from .reentry import cycles_from_ledger
from .trend import build_signals


def trial_key(row):
    return tuple(str(row[k]) for k in ('study','portfolio','window','start','end','cash_rate'))


def audit_trial(result, path, ledger, prices, weights, settings, strategy, signals, target, drop):
    """Rebuild terminal holdings, cash, receivables and costs from actual events."""
    cash_events={'contribution','buy','sell','distribution_payment'}
    cash=sum(e['amount'] for e in ledger if e['event'] in cash_events)+result['cash_interest']
    assert abs(cash-result['final_cash'])<1e-5
    assert abs(sum(e['amount'] for e in ledger if e['event']=='contribution')-result['contributed_capital'])<1e-6
    earned=sum(e['amount'] for e in ledger if e['event']=='distribution_entitlement')
    paid=sum(e['amount'] for e in ledger if e['event']=='distribution_payment')
    assert abs(earned-result['distribution_entitlements'])<1e-6
    assert abs(earned-paid-result['final_receivables'])<1e-5
    units={s:0. for s in weights};fees=0.;slippage=0.
    days=[p['date'] for p in path];next_day=dict(zip(days,days[1:]))
    first_by_month={}
    for d in days:first_by_month.setdefault(d[:7],d)
    exit_signal=None;entry_signal=None;entry_day=None
    for e in ledger:
        kind=e['event'];day=e['date'];s=e['symbol']
        if kind=='exit_signal':
            exit_signal=day
            if strategy=='trend':assert signals.get(day) is False
            else:assert e['amount']+1e-10>=target
        elif kind in ('entry_signal','reentry_signal'):
            entry_signal=day
            if strategy=='trend':assert signals.get(day) is True
            else:assert e['amount']<=-drop+1e-10
        elif kind in ('entry_fill','reentry_fill'):
            assert entry_signal and next_day.get(entry_signal)==day
            entry_day=day
        elif kind=='exit_fill':
            assert exit_signal and next_day.get(exit_signal)==day
        elif kind=='split':units[s]=e['units']
        elif kind in ('buy','sell'):
            side=1 if kind=='buy' else -1
            expected=prices[s][day]['open']*(1+side*settings['slippage'])
            assert abs(e['price']-expected)<1e-8
            expected_amount=-side*e['units']*e['price']-settings['brokerage']
            assert abs(e['amount']-expected_amount)<1e-7
            if kind=='sell':assert exit_signal and next_day.get(exit_signal)==day
            else:assert day==days[0] or day==first_by_month[day[:7]] or day==entry_day
            units[s]+=side*e['units'];assert units[s]>=-1e-8
            fees+=settings['brokerage'];slippage+=e['units']*prices[s][day]['open']*settings['slippage']
    assert abs(fees-result['brokerage_paid'])<1e-7
    assert abs(slippage-result['slippage_paid'])<1e-7
    wealth=cash+result['final_receivables']+sum(max(0,units[s]*prices[s][days[-1]]['close']*(1-settings['slippage'])-settings['brokerage']) for s in weights if units[s]>1e-8)
    assert abs(wealth-result['final_wealth'])<1e-5
    assert abs(wealth-result['contributed_capital']-result['profit'])<1e-5


def definitions(rules, signals):
    target=rules['exit_threshold'];drop=rules['reentry_drop']
    return [('hold','hold',{}),('exit_cash','target',dict(threshold=target)),
            ('fixed_reentry','fixed',dict(threshold=target,reentry_drop=drop)),
            ('peak_reentry','peak',dict(threshold=target,reentry_drop=drop,reentry_reference='peak')),
            ('trend','trend',dict(trend_signals=signals))]


def names(rules):
    return dict(hold='Buy-and-hold',exit_cash=f'Exit {rules["exit_threshold"]:.0%}, stay cash',
                fixed_reentry=f'Exit {rules["exit_threshold"]:.0%}, fixed dip {rules["reentry_drop"]:.0%}',
                peak_reentry=f'Exit {rules["exit_threshold"]:.0%}, peak dip {rules["reentry_drop"]:.0%}',
                trend=f'{rules["moving_average_months"]}-month trend')


def prior_results(root, config):
    old={}
    for folder,alias in [('results',{'hold':'hold','exit_20':'exit_cash'}),
                         ('results/reentry',{'exit_20_reenter_15':'fixed_reentry'})]:
        manifest=json.loads((root/folder/'run_manifest.json').read_text())
        if manifest['configuration']!=config:continue
        with open(root/folder/'trials.csv') as f:
            for r in csv.DictReader(f):
                if r['strategy'] in alias:old[(trial_key(r),alias[r['strategy']])]=r
    return old


def run(root, config, rules):
    validate_config(config)
    if rules['trend_initial_state_without_history']!='cash' or rules['target_reset']!='cycle_capital':
        raise ValueError('Unsupported initial state or gain accounting')
    if rules['peak_reference']!='highest_post_exit_closing_total_return_basket':raise ValueError('Unsupported peak reference')
    lookback=rules['moving_average_months'];target=rules['exit_threshold'];drop=rules['reentry_drop']
    if target<=0 or not 0<drop<1:raise ValueError('Invalid gain or drop threshold')
    prices,distributions,audit,gaps,common=prepare_data(root,config)
    out=root/'results/tactical';out.mkdir(parents=True,exist_ok=True)
    studies=[('main',config['portfolios'],config['initial_capital']),
             ('supplemental',config['supplemental']['portfolios'],config['supplemental']['initial_capital'])]
    signals_by_weights={};history=[]
    for study,portfolios,_ in studies:
        for name,weights in portfolios.items():
            key=tuple(sorted(weights.items()))
            if key not in signals_by_weights:signals_by_weights[key]=build_signals(prices,distributions,weights,lookback)
            signals,records,ready=signals_by_weights[key]
            history.extend(dict(study=study,portfolio=name,**r) for r in records)
    ready_dates=[signals_by_weights[tuple(sorted(w.items()))][2] for w in config['portfolios'].values()]
    common_ready=max(common,*ready_dates) if all(ready_dates) else None
    rows=[];events=[];cycles=[];daily=[];plot_paths={};checks=0
    for study,portfolios,capital in studies:
        settings={**config,'initial_capital':capital}
        for name,weights in portfolios.items():
            signals,_,ready=signals_by_weights[tuple(sorted(weights.items()))]
            windows=make_windows(prices,weights,config,common)
            finish=min(config['end'],*(max(prices[s]) for s in weights))
            if common_ready and common_ready<finish:windows.add(('common_ready',common_ready,finish))
            print(f'Tactical: {study}: {name}: {len(windows)} windows; trend ready {ready}',flush=True)
            for window,begin,end in sorted(windows):
                for rate in config['cash_rates']:
                    baseline=None;fixed=None
                    for strategy,mode,kwargs in definitions(rules,signals):
                        result,path,ledger=simulate(prices,distributions,weights,begin,end,settings,cash_rate=rate,**kwargs)
                        audit_trial(result,path,ledger,prices,weights,settings,strategy,signals,target,drop);checks+=1
                        if baseline is None:baseline=result
                        assert result['contributed_capital']==baseline['contributed_capital']
                        extra=dict(completed_reentries=0,pending_reentry=0,waiting_for_reentry=0,cash_days=0,
                                   last_exit_date='',last_entry_date='',waiting_days=0,completed_entries=0,in_cash=0,pending_initial_entry=0)
                        extra.update(result)
                        if mode in ('hold','target'):
                            extra['last_entry_date']=result['start'];extra['last_exit_date']=result['exit_date']
                            if result['exit_date']:
                                extra['cash_days']=(date.fromisoformat(result['end'])-date.fromisoformat(result['exit_date'])).days
                                extra['in_cash']=1
                        elif mode in ('fixed','peak'):extra['in_cash']=int(path[-1]['state']=='cash')
                        if mode!='trend':extra['completed_entries']=int(any(e['event']=='buy' for e in ledger))+extra['completed_reentries']
                        if strategy=='fixed_reentry':fixed=extra
                        warmup=0
                        if strategy=='trend':
                            extra['time_to_target_days']='';extra['never_reached_target']=''
                            boundary=min(ready or result['end'],result['end'])
                            warmup=max(0,(date.fromisoformat(boundary)-date.fromisoformat(result['start'])).days)
                        metadata=dict(study=study,portfolio=name,window=window,cash_rate=rate,strategy=strategy)
                        row=dict(**metadata,**extra,wealth_minus_hold=result['final_wealth']-baseline['final_wealth'],
                                 data_gap_affected=int(any(result['start']<=d<=result['end'] for d in gaps)),
                                 trend_ready_date=ready if strategy=='trend' else '',trend_warmup_cash_days=warmup,
                                 history_type='actual ETF holdings; constructed signal index where stated')
                        rows.append(row)
                        detail=window in ('full','common','common_ready') or (study=='main' and name=='NDQ' and window in ('12m','24m') and result['start'][:7] in ('2018-01','2020-01','2022-01'))
                        if detail:
                            detail_meta=dict(**metadata,trial_start=result['start'],trial_end=result['end'])
                            events.extend(dict(**detail_meta,**e) for e in ledger)
                            cycles.extend(cycles_from_ledger(detail_meta,ledger,result['end']))
                        if study=='main' and rate==0 and window in ('common','common_ready'):
                            plot_paths[(name,window,strategy)]=path
                            for p in path:
                                point=dict(cycle_capital='',cycle_gain='',state='cash' if result['exit_date'] and p['date']>=result['exit_date'] else 'invested',reference_value='',exit_reference='',reference_peak='')
                                point.update(p)
                                daily.append(dict(portfolio=name,window=window,strategy=strategy,**point))
    old=prior_results(root,config);regressions=0
    paired={}
    for r in rows:paired[(trial_key(r),r['strategy'])]=r
    for r in rows:
        k=trial_key(r)
        r['wealth_minus_fixed_reentry']=r['final_wealth']-paired[(k,'fixed_reentry')]['final_wealth']
        previous=old.get((k,r['strategy']))
        if previous is not None and target==.20 and drop==.15:
            # This study retains the existing capital/configuration defaults.
            assert float(previous['contributed_capital'])==r['contributed_capital']
            for field in ('final_wealth','profit','money_weighted_return','maximum_drawdown','brokerage_paid','distribution_entitlements'):
                assert abs(float(previous[field])-r[field])<1e-7,(k,r['strategy'],field)
            regressions+=1
    write_csv(out/'trials.csv',rows);write_csv(out/'trade_ledger.csv',events)
    write_csv(out/'cycles.csv',cycles);write_csv(out/'common_daily.csv',daily)
    write_csv(out/'trend_history.csv',history)
    groups=defaultdict(list)
    for r in rows:
        if not r['window'].endswith('m'):continue
        cohorts=['all_available']+(['common_ready_entries'] if common_ready and r['start']>=common_ready else [])
        for cohort in cohorts:
            groups[(r['study'],cohort,r['portfolio'],r['window'],r['cash_rate'],r['strategy'],r['data_gap_affected'])].append(r)
    summary=[]
    for key,group in sorted(groups.items()):
        study,cohort,name,window,rate,strategy,gap=key
        summary.append(dict(study=study,cohort=cohort,portfolio=name,window=window,cash_rate=rate,strategy=strategy,data_gap_affected=gap,
            trials=len(group),median_final_wealth=statistics.median(r['final_wealth'] for r in group),
            median_mwr=statistics.median(r['money_weighted_return'] for r in group),
            median_wealth_minus_hold=statistics.median(r['wealth_minus_hold'] for r in group),
            median_wealth_minus_fixed_reentry=statistics.median(r['wealth_minus_fixed_reentry'] for r in group),
            beat_hold=sum(r['wealth_minus_hold']>1e-6 for r in group),
            median_drawdown=statistics.median(r['maximum_drawdown'] for r in group),worst_drawdown=min(r['maximum_drawdown'] for r in group),
            completed_exits=sum(r['completed_exits'] for r in group),completed_reentries=sum(r['completed_reentries'] for r in group),
            median_cash_days=statistics.median(r['cash_days'] for r in group),in_cash_at_end=sum(r['in_cash'] for r in group)))
    write_csv(out/'summary.csv',summary)
    labels=names(rules)
    for i,name in enumerate(config['portfolios']):
        for window in ('common','common_ready'):
            if (name,window,'hold') not in plot_paths:continue
            series=[]
            for strategy in ('hold','fixed_reentry','peak_reentry','trend'):
                path=plot_paths[(name,window,strategy)];origin=date.fromisoformat(path[0]['date'])
                series.append((labels[strategy],[((date.fromisoformat(p['date'])-origin).days,p['wealth']) for p in path]))
            chart(out/f'wealth_{i+1}_{window}.svg',f'{name}: peak re-entry and monthly trend',series,
                  f'AUD; {path[0]["date"]} to {path[-1]["date"]}; cash 0%; data gaps flagged')
    write_report(out,rows,summary,common,common_ready,gaps,config,rules,ready_dates)
    inputs=[root/'config.json',root/'config_tactical.json',*sorted((root/'data/raw').glob('*')),
            *sorted((root/'data/normalized').glob('*')),*sorted((root/'etf_backtest').glob('*.py')),*sorted((root/'tests').glob('*.py'))]
    in_hash={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs if p.is_file()}
    output_hash={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.suffix in ('.csv','.svg') or p.name=='report.md'}
    (out/'run_manifest.json').write_text(json.dumps(dict(configuration=config,rules=rules,common_start=common,common_ready_start=common_ready,
        excluded_dates=gaps,trial_count=len(rows),sha256=in_hash,output_sha256=output_hash),indent=2)+'\n')
    (out/'validation.json').write_text(json.dumps(dict(status='passed; source gaps remain disclosed',trials_reconciled=checks,
        previous_results_matching=regressions,checks=['cash, holdings and receivables reconstructed','every order price, brokerage and slippage checked',
        'exit and entry fills on next available session','trend signals only from completed month ends','paired contribution equality'],excluded_dates=gaps),indent=2)+'\n')
    print(f'Wrote {len(rows)} tactical scenarios; {regressions} prior results matched',flush=True)


def write_report(out,rows,summary,common,common_ready,gaps,config,rules,ready_dates):
    labels=names(rules);periods=[('common','Same start as previous study')]
    if common_ready:periods.append(('common_ready','All portfolios have enough trend history'))
    lines=['# Peak-based re-entry and monthly trend allocation — pre-tax','',
        f'Actual ETF data through {config["end"]}. Main accounts start with A${config["initial_capital"]:,.0f} and receive A${config["monthly_contribution"]:,.0f} monthly from the following month. Same five main portfolios and A$10,000 supplemental accounts as previous studies. Results are in nominal AUD. No ETF history is extended before inception.','',
        '**Data qualification:** missing sessions '+', '.join(gaps)+' are omitted without inventing prices. Affected windows are flagged; missed signals, delayed fills and understated drawdowns remain possible. These are qualified historical results, not forecasts.','',
        '## Exact strategies','',
        '- **Buy-and-hold:** remains invested and buys monthly.',
        f'- **Exit/cash and fixed re-entry:** prior controls. Exit at {rules["exit_threshold"]:.0%} cycle gain; either stay in cash permanently or re-enter after a {rules["reentry_drop"]:.0%} decline from the exit basket value.',
        f'- **Peak re-entry:** retain the same {rules["exit_threshold"]:.0%} exit. While out, track the exact units sold, split-adjusted and including subsequent hypothetical cash distributions without reinvestment. Initialise the peak from the exit day’s closing basket value, then update it only with later closes. Re-enter when the current closing value is {rules["reentry_drop"]:.0%} below this running high. Opening/intraday highs are excluded. Buying back above the sale value is permitted. Reference distributions never enter actual account cash.',
        f'- **Monthly trend:** construct a monthly rebalanced, target-weight portfolio total-return index from actual ETF closes, splits and cash distributions. Signal-index distributions reinvest on the ex-date; this is only a signal convention. Actual account distributions still become cash on issuer payment dates. At each completed month-end, hold ETFs if the index is strictly above its {rules["moving_average_months"]}-month simple moving average, including that month’s close; otherwise hold cash. Equality means cash. There is no profit-target exit in this strategy.',
        f'- **Execution:** all new signals execute at the next available session’s open with A${config["brokerage"]:g} per ETF order and {config["slippage"]*10000:g}bp adverse slippage. The initial trend allocation uses only the latest signal strictly before the account’s first opening trade. Prices can rebound before a pending buy or gap down before a sell; orders are still executed. Final-day orders remain pending.',
        '- **Contributions and resets:** contributions continue identically while in cash. Peak/fixed re-entry invests affordable cash at target weights and resets cycle capital to account wealth just before buying, including accumulated contributions and any actual distribution receivables. Contributions while invested raise cycle capital; profit targets are not measured against lifetime gains after a reset.',
        '- **Monthly purchases:** active accounts buy whole units with new cash at the first available monthly open, using allocation deficits. There are no routine sales to rebalance the actual account. The monthly rebalancing above applies only to the signal index. Fund expenses are embedded in prices; they are not deducted again.','',
        '## Signal warm-up','',
        f'The inception month is excluded as a conservative stub. Ten complete monthly closes are required with the default lookback; no signal or account buys are generated before the history is sufficient. A missing VGS quote on 31 December 2014 prevents a valid mixed-portfolio month-end observation: it is omitted, that signal-index rebalance is skipped, and the consecutive-month warm-up restarts. No December value is imputed. This pre-test history issue is recorded in `trend_history.csv` and delays Vanguard readiness. The last partial cached month does not generate a signal. A new account with adequate history uses its latest already-known allocation; a new account without it stays in cash. Ready dates below indicate the first opening session after the first valid moving-average decision, which can itself be bearish.','',
        '| Portfolio | First session with sufficient trend history |','|---|---|']
    for name,ready in zip(config['portfolios'],ready_dates):lines.append(f'| {name} | {ready or "Unavailable"} |')
    lines+=['',f'The same-start comparison begins {common}; the warm-up-free common comparison begins {common_ready or "unavailable"}. The latter resets all accounts to identical starting capital on that later date, rather than carrying earlier gains forward. This isolates a comparison where every portfolio has enough signal history.','']
    for window,title in periods:
        group=[r for r in rows if r['study']=='main' and r['window']==window and r['cash_rate']==0]
        lines += [f'## {title}', '',
            'Cash earns 0%. Wealth includes estimated terminal liquidation costs; XIRR is annualised and drawdown is adjusted for contributions. Cash days are calendar days fully out of ETF holdings, including initial warm-up where applicable. Each table crosses source-data gaps.','',
            '| Portfolio | Strategy | Wealth | Contributed | Profit | MWR/year | Max drawdown | Entries | Exits | Re-entries | Cash days | Warm-up days |',
            '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for r in group:
            lines.append(f'| {r["portfolio"]} | {labels[r["strategy"]]} | {r["final_wealth"]:,.0f} | {r["contributed_capital"]:,.0f} | {r["profit"]:,.0f} | {pct(r["money_weighted_return"])} | {pct(r["maximum_drawdown"])} | {r["completed_entries"]} | {r["completed_exits"]} | {r["completed_reentries"]} | {r["cash_days"]} | {r["trend_warmup_cash_days"]} |')
        lines += ['']
        for strategy in ('peak_reentry','trend'):
            selected=[r for r in group if r['strategy']==strategy]
            lines.append(f'{labels[strategy]} beat buy-and-hold on final wealth in {sum(r["wealth_minus_hold"]>1e-6 for r in selected)} of {len(selected)} portfolios. It completed {sum(r["completed_reentries"] for r in selected)} re-entries. These portfolios share underlying holdings and market periods; they are not independent observations.')
        lines+=['']
    lines+=['## What the results mean','',
        f'Peak-based re-entry addresses the old rule’s dependence on the original sale price. It can re-enter following a correction even when the market is still above that sale. It still caps gains at each {rules["exit_threshold"]:.0%} exit and can remain in cash while prices rise. The profit target provides no downside protection before it is reached. A completed re-entry can be followed by further losses.', '',
        'The monthly trend rule allows winners to continue beyond 20% and changes allocation only after a month-end signal. It reacts with a lag, can sell after a substantial decline, can miss a fast rebound, and can repeatedly buy and sell in sideways markets. Cash exposure and lower observed drawdown are not guarantees of capital protection. The same-start BGBL trend results include a long warm-up in cash; compare the second table to assess outcomes without that initial-history difference.', '',
        'These are illustrative rules inspired by systematic investing, not replicas of AQR, Man AHL or any named fund. No parameter optimisation or claim of the best rule is made.','',
        '## Different market conditions','',
        'Selected 12-month accounts beginning January 2020 or January 2022, 0% cash. BGBL funds have no history in these periods and are omitted. These examples are not pooled with common-period results.','',
        '| Entry | Portfolio | Strategy | Wealth | Contributed | MWR/year | Max drawdown | Exits | Re-entries |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        if r['study']=='main' and r['cash_rate']==0 and r['window']=='12m' and r['start'][:7] in ('2020-01','2022-01'):
            lines.append(f'| {r["start"]} | {r["portfolio"]} | {labels[r["strategy"]]} | {r["final_wealth"]:,.0f} | {r["contributed_capital"]:,.0f} | {pct(r["money_weighted_return"])} | {pct(r["maximum_drawdown"])} | {r["completed_exits"]} | {r["completed_reentries"]} |')
    lines+=['','## Rolling 12-month accounts after common signal readiness','',
        'Monthly entry cohorts, main study, 0% cash. Complete and gap-affected windows are separated. Overlapping accounts are dependent; hit counts and win counts are descriptive, not future probabilities. Median drawdown can mask more severe losses in individual trials.','',
        '| Portfolio | Strategy | Gap affected | Accounts | Beat hold | Median wealth vs hold | Median drawdown | Worst drawdown | Median cash days |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for r in summary:
        if r['study']=='main' and r['cohort']=='common_ready_entries' and r['window']=='12m' and r['cash_rate']==0 and r['strategy'] in ('peak_reentry','trend'):
            lines.append(f'| {r["portfolio"]} | {labels[r["strategy"]]} | {bool(r["data_gap_affected"])} | {r["trials"]} | {r["beat_hold"]} | {r["median_wealth_minus_hold"]:,.0f} | {pct(r["median_drawdown"])} | {pct(r["worst_drawdown"])} | {r["median_cash_days"]} |')
    lines+=['','## Hypothetical 3% cash sensitivity','',
        'Common-ready accounts. This is a constant assumed nominal yield, not historical deposit rates. Buy-and-hold at the same rate remains the paired baseline.','',
        '| Portfolio | Strategy | Wealth | Wealth vs same-rate hold | Max drawdown |',
        '|---|---|---:|---:|---:|']
    for r in rows:
        if r['study']=='main' and r['window']=='common_ready' and r['cash_rate']==.03 and r['strategy'] in ('hold','peak_reentry','trend'):
            lines.append(f'| {r["portfolio"]} | {labels[r["strategy"]]} | {r["final_wealth"]:,.0f} | {r["wealth_minus_hold"]:,.0f} | {pct(r["maximum_drawdown"])} |')
    lines+=['','## Files and limitations','',
        '`trials.csv` includes every full-history, annual-start, monthly 3/6/12/24-month and quarterly 36/60-month account plus both common starts, including the supplemental A$10,000 study. Only complete rolling horizons are included. `summary.csv` separates `all_available` from `common_ready_entries` cohorts; they overlap and must not be pooled. `common_daily.csv` includes portfolio state, cycle capital and reference peaks for both main common windows. `trend_history.csv` provides month-end signal values and moving averages. This index is constructed from actual ETF returns for signals; it is not an actual fund or a proxy extending pre-inception history.', '',
        '`trade_ledger.csv` and `cycles.csv` retain full/common/common-ready accounts and selected NDQ January 2018/2020/2022 rolling examples. Initial trend entries following warm-up use `entry_fill`; later purchases after an exit use `reentry_fill`. Entries include the initial investment; re-entries exclude it. `signal_date`/`exit_date` refer to the first exit. The legacy `time_to_target_days` field is not applicable to trend allocation. Charts are in `wealth_*.svg`; identical lines can overlap.','',
        'All results exclude personal CGT, income tax, franking-credit benefits, AMIT cost-base changes and inflation. Trading more often can create additional taxable gains. Brokerage/slippage, liquidity and immediately available sale proceeds are assumptions; settlement or broker rules may defer a rapid re-entry. Signal-index ex-date reinvestment is a mathematical convention, not an assertion that actual distributions were spendable before payment. Individual ETFs, allocations and thresholds were selected retrospectively. The short common-ready history does not establish performance over a full market cycle. Future losses may exceed all observed drawdowns.','',
        'Every trial is checked by rebuilding cash, final holdings, distribution receivables, order prices and costs from events. Initial trend decisions use only earlier completed month-end signals. Runtime checks enforce next-available-session execution. Tests cover warm-up, future-data independence, equality, distributions, splits, peak anchors and repeated cycles. Input/output hashes and validation results are saved alongside this report.']
    (out/'report.md').write_text('\n'.join(lines)+'\n')


def validate(root):
    import xml.etree.ElementTree as ET
    out=root/'results/tactical';manifest=json.loads((out/'run_manifest.json').read_text())
    for rel,h in manifest['sha256'].items():
        if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=h:raise ValueError(f'Input changed: {rel}; rerun tactical')
    for rel,h in manifest['output_sha256'].items():
        if hashlib.sha256((out/rel).read_bytes()).hexdigest()!=h:raise ValueError(f'Output changed: {rel}; rerun tactical')
    with open(out/'trials.csv') as f:rows=list(csv.DictReader(f))
    with open(out/'trade_ledger.csv') as f:events=list(csv.DictReader(f))
    with open(out/'common_daily.csv') as f:daily=list(csv.DictReader(f))
    group=defaultdict(list)
    for e in events:group[(e['study'],e['portfolio'],e['window'],e['cash_rate'],e['strategy'],e['trial_start'],e['trial_end'])].append(e)
    baselines={trial_key(r):r for r in rows if r['strategy']=='hold'}
    count=0
    for r in rows:
        assert r['contributed_capital']==baselines[trial_key(r)]['contributed_capital']
        assert abs(float(r['final_wealth'])-float(r['contributed_capital'])-float(r['profit']))<1e-5
        e=group.get((r['study'],r['portfolio'],r['window'],r['cash_rate'],r['strategy'],r['start'],r['end']))
        if e is not None:
            cash=sum(float(x['amount']) for x in e if x['event'] in ('contribution','buy','sell','distribution_payment'))+float(r['cash_interest'])
            assert abs(cash-float(r['final_cash']))<1e-5
            assert sum(x['event']=='exit_fill' for x in e)==int(r['completed_exits']) if r['strategy'] in ('fixed_reentry','peak_reentry','trend') else True
            assert sum(x['event']=='reentry_fill' for x in e)==int(r['completed_reentries'])
            count+=1
    for p in daily:
        if p['strategy']=='trend':
            assert p['state'] in ('cash','invested')
        elif p['strategy']=='peak_reentry' and p['state']=='cash':
            assert float(p['reference_peak'])+1e-7>=float(p['reference_value'])
    charts=list(out.glob('wealth_*.svg'))
    for chart_path in charts:ET.parse(chart_path)
    result=dict(status='passed; source gaps remain disclosed',trials_checked=len(rows),retained_ledgers_reconciled=count,
        input_hashes_verified=len(manifest['sha256']),output_hashes_verified=len(manifest['output_sha256']),svg_charts_parsed=len(charts))
    (out/'independent_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
