"""Independent reconciliation of generated artifacts and cached input hashes."""
import csv
from collections import defaultdict
import hashlib
import json
import math
import xml.etree.ElementTree as ET


def validate(root):
    out=root/'results'
    manifest=json.loads((out/'run_manifest.json').read_text())
    for path,expected in manifest['sha256'].items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=expected:
            raise ValueError(f'Input changed since run: {path}; rerun analysis')
    with open(out/'trials.csv') as f:trials=list(csv.DictReader(f))
    with open(out/'trade_ledger.csv') as f:ledger=list(csv.DictReader(f))
    events=defaultdict(list)
    for e in ledger:
        key=tuple(e[k] for k in ('study','portfolio','window','cash_rate','strategy'))
        events[key].append(e)
    counts=defaultdict(int)
    for r in trials:
        wealth=float(r['final_wealth']);capital=float(r['contributed_capital'])
        assert math.isfinite(wealth) and wealth>=0
        assert abs(wealth-capital-float(r['profit']))<1e-6
        assert int(r['completed_exits'])<=1
        if r['exit_date']:assert r['exit_date']>r['signal_date']
        if r['strategy']!='hold':assert bool(r['signal_date']) != bool(int(r['never_reached_target']))
        counts['trials_checked']+=1
        if r['window'] not in ('common','full'):continue
        key=tuple(r[k] for k in ('study','portfolio','window','cash_rate','strategy'))
        group=events[key]
        paid_capital=sum(float(e['amount']) for e in group if e['event']=='contribution')
        assert abs(paid_capital-capital)<1e-6
        # Entitlements are not cash flows. Purchases/sales include brokerage.
        cash=sum(float(e['amount']) for e in group if e['event'] in ('contribution','buy','sell','distribution_payment'))+float(r['cash_interest'])
        assert abs(cash-float(r['final_cash']))<1e-5,(key,cash,r['final_cash'])
        earned=sum(float(e['amount']) for e in group if e['event']=='distribution_entitlement')
        assert abs(earned-float(r['distribution_entitlements']))<1e-6
        assert sum(e['event']=='exit_signal' for e in group)==bool(r['signal_date'])
        counts['ledgers_reconciled']+=1
    for chart in out.glob('wealth_*.svg'):
        ET.parse(chart);counts['svg_charts_parsed']+=1
    counts['input_hashes_verified']=len(manifest['sha256'])
    counts['status']='passed; source data gaps remain disclosed'
    (out/'validation.json').write_text(json.dumps(dict(counts),indent=2)+'\n')
    print(json.dumps(dict(counts),indent=2))
