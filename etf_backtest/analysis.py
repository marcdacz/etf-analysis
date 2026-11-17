"""Scenario generation, paired comparisons, reproducible CSVs and SVG charts."""
from collections import defaultdict
from datetime import date, timedelta
from html import escape
import hashlib
import json
import statistics
from .data import load, write_csv
from .engine import add_months, simulate


def pct(x):return 'n/a' if x is None or x=='' else f'{x:.2%}'


def chart(path, title, series, ylabel):
    """Standalone SVG; no browser, plotting dependencies or remote assets."""
    colors=['#2563eb','#b45309','#15803d','#7e22ce','#b91c1c','#0e7490']
    values=[v for _,points in series for _,v in points]
    low=min(0,min(values));high=max(values);span=high-low or 1
    maxx=max(x for _,points in series for x,_ in points) or 1
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="620" viewBox="0 0 1100 620" role="img">',f'<title>{escape(title)}</title>', '<rect width="1100" height="620" fill="white"/>',f'<text x="80" y="32" font-family="sans-serif" font-size="20">{escape(title)}</text>',f'<text x="80" y="58" font-family="sans-serif" font-size="13">{escape(ylabel)}</text>']
    for i in range(6):
        val=low+span*i/5;y=470-(val-low)/span*380
        svg.extend([f'<line x1="80" y1="{y}" x2="1040" y2="{y}" stroke="#ddd"/>',f'<text x="72" y="{y+4}" text-anchor="end" font-size="12" font-family="sans-serif">{val:,.0f}</text>'])
    for i,(label,points) in enumerate(series):
        coords=' '.join(f'{80+x/maxx*960:.1f},{470-(v-low)/span*380:.1f}' for x,v in points)
        color=colors[i%len(colors)]
        svg.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2"/>')
        y=520+(i//3)*24;x=80+(i%3)*330
        svg.extend([f'<line x1="{x}" y1="{y}" x2="{x+24}" y2="{y}" stroke="{color}" stroke-width="3"/>',f'<text x="{x+32}" y="{y+4}" font-family="sans-serif" font-size="12">{escape(label)}</text>'])
    svg.append(f'<text x="560" y="498" text-anchor="middle" font-family="sans-serif" font-size="13">Calendar days since start (0 to {maxx})</text></svg>')
    path.write_text('\n'.join(svg))


def validate_config(c):
    if c['start']>=c['end']:raise ValueError('start must precede end')
    for key in ['initial_capital','monthly_contribution','brokerage','slippage']:
        if c[key]<0:raise ValueError(f'{key} must be nonnegative')
    if c['initial_capital']<=0 or c['slippage']>=1:raise ValueError('Invalid capital/slippage')
    for w in list(c['portfolios'].values())+list(c['supplemental']['portfolios'].values()):
        if abs(sum(w.values())-1)>1e-9 or min(w.values())<=0:raise ValueError('Weights must be positive and sum to 1')
    if any(r<0 for r in c['cash_rates']):raise ValueError('Cash rates must be nonnegative')


def prepare_data(root, config):
    prices,distributions=load(root)
    audit=json.loads((root/'data/normalized/audit.json').read_text())
    # Dates present for some funds but absent for others, after all funds exist.
    # Also include earlier missing dates when another ETF was already trading.
    union=set().union(*(set(p) for p in prices.values()))
    gaps=sorted(d for d in union if config['start']<=d<=config['end'] and any(min(p)<=d<=max(p) and d not in p for p in prices.values()))
    # A zero-volume placeholder may coincide with empty records in every other
    # fund, so it would disappear from the normalized union. Keep that gap too.
    gaps=sorted(set(gaps).union(d for a in audit for d in a['excluded_zero_volume_dates']
        if config['start']<=d<=config['end'] and a['first_price']<d<a['last_price']))
    # No forward fill: omit known incomplete dates consistently for ALL strategies.
    filtered={s:{d:q for d,q in p.items() if d not in gaps} for s,p in prices.items()}
    for s in filtered:
        for div in distributions[s]:
            if div['ex_date'] in gaps:raise ValueError('Cannot skip a distribution ex-date')
    common=max(config['start'],*(min(p) for p in filtered.values()))
    return filtered,distributions,audit,gaps,common


def make_windows(filtered, weights, config, common):
    earliest=max(config['start'],*(min(filtered[s]) for s in weights))
    available_end=min(config['end'],*(max(filtered[s]) for s in weights))
    windows={('full',earliest,available_end),('common',max(common,earliest),available_end)}
    for year in range(date.fromisoformat(earliest).year,date.fromisoformat(available_end).year+1):
        begin=f'{year}-01-01'
        if earliest<=begin<available_end:windows.add(('annual',begin,available_end))
    # Full monthly entry cohorts for 3/6/12/24m; quarterly for 3/5y.
    begin=add_months(earliest,0)
    if begin<earliest:begin=add_months(begin,1)
    while begin<available_end:
        for months in config['horizon_months']:
            if months>24 and date.fromisoformat(begin).month not in (1,4,7,10):continue
            boundary=add_months(begin,months)
            if boundary<=available_end:
                finish=(date.fromisoformat(boundary)-timedelta(days=1)).isoformat()
                windows.add((f'{months}m',begin,finish))
        begin=add_months(begin,1)
    return windows


def run(root, config):
    validate_config(config)
    filtered,distributions,audit,gaps,common=prepare_data(root,config)
    out=root/'results';out.mkdir(exist_ok=True)
    (out/'data_gaps.json').write_text(json.dumps(dict(excluded_dates=gaps,policy='No imputation; affected windows explicitly flagged. Signals/fills may be delayed over omitted sessions.'),indent=2)+'\n')
    rows=[];full_paths={};full_ledgers=[]
    studies=[('main',config['portfolios'],config['initial_capital']),('supplemental',config['supplemental']['portfolios'],config['supplemental']['initial_capital'])]
    for study,portfolios,capital in studies:
        settings={**config,'initial_capital':capital}
        for name,weights in portfolios.items():
            windows=make_windows(filtered,weights,config,common)
            print(f'{study}: {name}: {len(windows)} windows',flush=True)
            for kind,begin,finish in sorted(windows):
                for rate in config['cash_rates']:
                    for target in config['thresholds']:
                        result,path,ledger=simulate(filtered,distributions,weights,begin,finish,settings,target,rate)
                        row=dict(study=study,portfolio=name,window=kind,cash_rate=rate,strategy='hold' if target is None else f'exit_{int(target*100)}',threshold='' if target is None else target,**result,
                            data_gap_affected=int(any(result['start']<=g<=result['end'] for g in gaps)),history_type='actual ETF')
                        rows.append(row)
                        if kind in ('full','common'):
                            for event in ledger:full_ledgers.append(dict(study=study,portfolio=name,window=kind,cash_rate=rate,strategy=row['strategy'],**event))
                        if study=='main' and kind=='common' and rate==0:
                            full_paths[(name,row['strategy'])]=path
    baseline={(r['study'],r['portfolio'],r['window'],r['start'],r['end'],r['cash_rate']):r for r in rows if r['strategy']=='hold'}
    for r in rows:
        b=baseline[(r['study'],r['portfolio'],r['window'],r['start'],r['end'],r['cash_rate'])]
        if r['contributed_capital']!=b['contributed_capital']:raise AssertionError('Unequal contributions')
        r['wealth_minus_hold']=r['final_wealth']-b['final_wealth']
        if abs(r['profit']-(r['final_wealth']-r['contributed_capital']))>1e-7:raise AssertionError('Profit mismatch')
        if r['exit_date'] and r['exit_date']<=r['signal_date']:raise AssertionError('Look-ahead fill')
    write_csv(out/'trials.csv',rows);write_csv(out/'trade_ledger.csv',full_ledgers)
    pathrows=[]
    for (name,strategy),path in full_paths.items():
        pathrows.extend(dict(portfolio=name,strategy=strategy,**p) for p in path)
    write_csv(out/'common_daily.csv',pathrows)
    grouped=defaultdict(list)
    for r in rows:
        # Comparable common cohorts for all five primary portfolios; exclude
        # incomplete trailing windows and distinguish source-gap contamination.
        if r['study']=='main' and r['window'].endswith('m') and r['start']>=common:
            grouped[(r['portfolio'],r['window'],r['cash_rate'],r['strategy'],r['data_gap_affected'])].append(r)
    summary=[]
    for (name,window,rate,strategy,gap),group in sorted(grouped.items()):
        reached=[r for r in group if r['signal_date']]
        summary.append(dict(portfolio=name,window=window,cash_rate=rate,strategy=strategy,data_gap_affected=gap,
            trials=len(group),targets_reached=len(reached),completed_exits=sum(r['completed_exits'] for r in group),
            never_reached=sum(r['never_reached_target'] for r in group),pending_exits=sum(r['pending_exit'] for r in group),
            target_hit_rate=len(reached)/len(group) if strategy!='hold' else '',
            median_time_to_target_days=statistics.median(r['time_to_target_days'] for r in reached) if reached else '',
            median_final_wealth=statistics.median(r['final_wealth'] for r in group),
            median_wealth_minus_hold=statistics.median(r['wealth_minus_hold'] for r in group),
            median_mwr=statistics.median(r['money_weighted_return'] for r in group),
            worst_drawdown=min(r['maximum_drawdown'] for r in group)))
    write_csv(out/'summary.csv',summary)
    for i,name in enumerate(config['portfolios']):
        ser=[]
        for strategy in ['hold','exit_15','exit_20']:
            path=full_paths[(name,strategy)];origin=date.fromisoformat(path[0]['date'])
            ser.append((strategy, [((date.fromisoformat(p['date'])-origin).days,p['wealth']) for p in path]))
        path=full_paths[(name,'hold')]
        ser.append(('contributed', [((date.fromisoformat(p['date'])-origin).days,p['contributed']) for p in path]))
        chart(out/f'wealth_{i+1}.svg',f'{name}: common period, cash 0% (data gaps flagged)',ser,'Liquidation wealth, AUD; initial A$20,000, then A$1,000 monthly')
    report(root,rows,summary,audit,gaps,common,config)
    # Pin inputs, config and source-code hashes for an auditable offline rerun.
    files=[root/'config.json',*sorted((root/'data/raw').glob('*')),*sorted((root/'data/normalized').glob('*')),*sorted((root/'etf_backtest').glob('*.py')),*sorted((root/'tests').glob('*.py'))]
    provenance={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
    (out/'run_manifest.json').write_text(json.dumps(dict(configuration=config,sha256=provenance,trial_count=len(rows),checks='paired contributions, next-session fills, profit identities, nonnegative cash'),indent=2)+'\n')
    print(f'Wrote {len(rows)} trials, {len(summary)} summary groups and report to {out}',flush=True)


def report(root,rows,summary,audit,gaps,common,c):
    lines=['# ETF accumulation backtest — pre-tax', '',
        f'Actual ETF history through {c["end"]}. Main study: A${c["initial_capital"]:,.0f} initially, A${c["monthly_contribution"]:,.0f} monthly from the following month. Restored from “Retrieve ETF Prices”; the earlier unexecuted script was not available in this workspace. Supplemental study retains the confirmed A$10,000 VAS/VGS comparisons.', '',
        '**Data qualification:** missing provider prices on '+', '.join(gaps)+'. No prices are fabricated or carried forward. These dates are omitted consistently; affected windows have `data_gap_affected=1`. A missed close could change a signal, a sale could be delayed, and maximum drawdown could be understated. Treat affected results as qualified estimates, not fully validated daily-history results. Summary CSV separates complete and affected windows.', '',
        '## Common-period comparison', '',
        f'All five portfolios start on {common}, the latest first available ETF price. Cash earns 0%. Final wealth includes estimated liquidation costs; ETF holdings are marked at the final close rather than sold by the strategy. All values AUD. This common window includes data gaps.', '',
        '| Portfolio | Strategy | Final wealth | Contributed | Profit | MWR/year | Max drawdown | Target days | Exits | Never hit |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        if r['study']=='main' and r['window']=='common' and r['cash_rate']==0:
            lines.append(f'| {r["portfolio"]} | {r["strategy"]} | {r["final_wealth"]:,.0f} | {r["contributed_capital"]:,.0f} | {r["profit"]:,.0f} | {pct(r["money_weighted_return"])} | {pct(r["maximum_drawdown"])} | {r["time_to_target_days"]} | {r["completed_exits"]} | {r["never_reached_target"]} |')
    lines+=['','## Reaching 20% within 12 months','','Monthly entry cohorts starting after the common inception date. These are historical frequencies, not probabilities of future success. Overlapping windows are dependent; gap status is shown separately.','', '| Portfolio | Gap affected | Trials | Reached | Completed exits | Never hit | Median days if hit | Median wealth vs hold |','|---|---|---:|---:|---:|---:|---:|---:|']
    for r in summary:
        if r['window']=='12m' and r['strategy']=='exit_20' and r['cash_rate']==0:
            lines.append(f'| {r["portfolio"]} | {bool(r["data_gap_affected"])} | {r["trials"]} | {r["targets_reached"]} ({pct(r["target_hit_rate"])}) | {r["completed_exits"]} | {r["never_reached"]} | {r["median_time_to_target_days"]} | {r["median_wealth_minus_hold"]:,.0f} |')
    lines+=['','## Longer history and market conditions','','Full and annual-start trials use each portfolio’s available history. Monthly 3/6/12/24-month windows and quarterly 36/60-month windows end before a calendar-month boundary. Short incomplete windows are excluded rather than counted as failures. Older funds include the COVID decline and 2022 sell-off; BGBL portfolios cannot represent either period. Annual-start trials have unequal lengths and must not be pooled as if comparable.','', '| Portfolio | History starts | Hold wealth | 15% exit date | 20% exit date |','|---|---|---:|---|---|']
    for name in c['portfolios']:
        group={r['strategy']:r for r in rows if r['study']=='main' and r['window']=='full' and r['cash_rate']==0 and r['portfolio']==name}
        lines.append(f'| {name} | {group["hold"]["start"]} | {group["hold"]["final_wealth"]:,.0f} | {group["exit_15"]["exit_date"] or "No completed exit"} | {group["exit_20"]["exit_date"] or "No completed exit"} |')
    lines += ['', 'Selected 12-month entry cohorts show outcomes through different market conditions (0% cash, A$20,000 initially). Funds without actual history are absent.', '', '| Entry year | Portfolio | Strategy | Final wealth | Contributed | Max drawdown | Target days | Never hit |', '|---|---|---|---:|---:|---:|---:|---:|']
    for r in rows:
        if r['study']=='main' and r['cash_rate']==0 and r['window']=='12m' and r['start'][:4] in ('2020','2022') and r['start'][5:7]=='01':
            lines.append(f'| {r["start"][:4]} | {r["portfolio"]} | {r["strategy"]} | {r["final_wealth"]:,.0f} | {r["contributed_capital"]:,.0f} | {pct(r["maximum_drawdown"])} | {r["time_to_target_days"]} | {r["never_reached_target"]} |')
    lines+=['','## Interpretation and trade-offs','']
    common_rows=[r for r in rows if r['study']=='main' and r['window']=='common' and r['cash_rate']==0 and r['strategy']!='hold']
    wins=sum(r['wealth_minus_hold']>0 for r in common_rows)
    lines.append(f'In the qualified common-period run, exiting beat buy-and-hold on final wealth in {wins} of {len(common_rows)} portfolio/threshold comparisons. This is one market path, not evidence of a universally better rule. The tables and paired `wealth_minus_hold` columns show the cost or benefit of each exit.')
    lines += ['', 'Hypothetical cash-yield sensitivity for the common period (all rows cross source-data gaps):', '', '| Portfolio | Strategy | Wealth, cash 0% | Wealth, cash 3% |', '|---|---|---:|---:|']
    for r in common_rows:
        counterpart=next((v for v in rows if v['study']=='main' and v['window']=='common' and v['portfolio']==r['portfolio'] and v['strategy']==r['strategy'] and v['cash_rate']==.03),None)
        if counterpart:lines.append(f'| {r["portfolio"]} | {r["strategy"]} | {r["final_wealth"]:,.0f} | {counterpart["final_wealth"]:,.0f} |')
    lines+=['','A lower target can secure gains sooner and shorten market exposure, but stops compounding once sold. A higher target can require longer waits and deeper interim losses. Continued contributions dilute percentage gains; they are never investment profit. A 20% portfolio target is not a 20% annual return. Concentrated NDQ exposure can produce a different path from diversified portfolios; adding NDQ overlaps global equity holdings. A200/VAS and BGBL/VGS track different universes and are not exact replicas.', '',
        'The 3% cash scenarios are hypothetical, constant nominal annual yields applied to all actual cash balances, including idle cash before an exit. They are not historical deposit rates. Compare them with their same-rate buy-and-hold baseline. No re-entry is modelled, so completed exits are at most one per trial. Rolling entry dates represent independent hypothetical accounts, not repeated exit/re-entry cycles.', '',
        '## Accounting and execution', '',
        '- Gain = (net liquidation wealth / cumulative external contributions) − 1. Wealth includes cash and earned unpaid distributions; selling costs are estimated for held positions. A$11,500 against A$10,000 is 15%; adding A$1,000 lowers it to 13.64%.',
        '- Month-one capital replaces the first monthly contribution. Subsequent A$1,000 contributions arrive before the first available session each month and continue after selling. No withdrawals.',
        '- Signals use the close; exit fills use the next available open plus adverse slippage. A final-day signal is reported as pending, not a completed exit. Realised gains can fall below target because of overnight moves.',
        '- Whole-unit purchases use fixed cash budgets proportional to allocation deficits, at scheduled opens; brokerage can leave cash idle. No routine selling to rebalance. Distributions reinvest at scheduled purchases only.',
        '- Holders before the ex-date opening receive entitlement. Payment dates release cash; selling between ex-date and payment preserves that receivable. No interest is earned on receivables. No dividend-adjusted prices are used.',
        '- Yahoo quote prices are split-adjusted; the loader reverses future split factors before the engine adjusts units on the split date. The cached actual series have no split events; synthetic fixtures test this path.',
        '- Fund expenses are embedded in observed prices and distributions, so management fees are not deducted again. A$5 per executed ETF order and 5 basis points adverse slippage are explicit assumptions.',
        '- Money-weighted return is annualised XIRR using dated contributions and terminal net wealth. Short-window annualised returns can be extreme. Drawdown uses a contribution-adjusted return index, with contributions at the beginning of a session; it includes costs and avoids contributions hiding losses.', '',
        '## Data and limitations', '',
        'Sources and SHA-256 hashes are in `data/raw/manifest.json`; original responses are cached. Normalised records and provider disagreements are in `data/normalized/`. Empty records and zero-volume quotes are excluded, including indicative quotes before first observed trading; these are listed in the audit. Issuer CASH distributions take precedence over Yahoo events, including corrected distribution dates and amounts. Tax credits and gross tax distributions are excluded from spendable cash. Raw records include data outside the chosen test interval; simulations never use future records for signals.', '',
        '| ETF | First cached price | Last usable price | Issuer distributions | Yahoo disagreements |','|---|---|---|---:|---:|']
    for a in audit:lines.append(f'| {a["symbol"]} | {a["first_price"]} | {a["last_price"]} | {a["distributions"]} | {len(a["discrepancies"])} |')
    lines+=['','No proxy or synthetic investment history is included in results. Synthetic values occur only in unit tests. BGBL has a short actual history; five-year BGBL comparisons are unavailable and omitted. There is survivorship/selection bias in choosing today’s funds and allocations, and no optimisation or out-of-sample claim.','','Missing/zero-volume provider records, rounded issuer distribution figures, unverified historical opening auction liquidity, settlement delays, spread changes, inflation and historical brokerage schedules limit realism. Cash from a sale is treated as immediately available; there is no re-entry, so settlement does not fund new purchases. Corporate actions and distribution data can be revised by providers; offline cached reruns preserve this snapshot, while `--refresh` intentionally changes it.','','Results exclude personal income tax, CGT, franking-credit refunds and AMIT cost-base adjustments. Tax modelling is not implemented; adding it requires explicit parcel-level assumptions and investor circumstances. No historical result guarantees future returns.','','## Files and validation','','`trials.csv` contains every scenario and metric; `summary.csv` separates common-period rolling cohorts by data quality; `trade_ledger.csv` contains full/common contributions, trades, entitlements and payments; `common_daily.csv` contains common-period wealth paths; `wealth_*.svg` are standalone charts. `run_manifest.json` pins configuration, source files and code hashes. Tests and runtime checks cover accounting and timing; data gaps remain unresolved as disclosed above.']
    (root/'results/report.md').write_text('\n'.join(lines)+'\n')
