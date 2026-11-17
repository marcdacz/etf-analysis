"""Download, cache, normalise and validate actual ETF records. No proxy fallback."""
import csv
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo

FUNDS = {'VAS': '8205', 'VGS': '8212', 'NDQ': 'nasdaq-100-etf',
         'A200': 'australia-200-etf', 'BGBL': 'global-shares-etf'}

def sources(symbol):
    price = f'https://query2.finance.yahoo.com/v8/finance/chart/{symbol}.AX?range=15y&interval=1d&events=div,splits'
    fund = FUNDS[symbol]
    dist = (f'https://www.vanguard.com.au/personal/api/data/products/product-distribution/{fund}'
            if symbol in ('VAS', 'VGS') else f'https://www.betashares.com.au/advisers/fund/{fund}/')
    return price, dist

def write_csv(path, rows):
    rows = list(rows)
    if not rows:
        raise ValueError(f'No records for {path}')
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def fetch(root, refresh=False):
    raw = root / 'data/raw'; raw.mkdir(parents=True, exist_ok=True)
    manifest_path = raw / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for symbol in FUNDS:
        for kind, url in zip(('prices', 'distributions'), sources(symbol)):
            ext = 'html' if kind == 'distributions' and symbol not in ('VAS', 'VGS') else 'json'
            path = raw / f'{symbol}-{kind}.{ext}'
            if refresh or not path.exists():
                temp = path.with_suffix('.download')
                subprocess.run(['curl', '-fLsS', '--retry', '2', '--max-time', '60', '-A', 'Mozilla/5.0', url, '-o', str(temp)], check=True)
                temp.replace(path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            old = manifest.get(path.name, {})
            manifest[path.name] = dict(url=url, sha256=digest,
                retrieved_at=old.get('retrieved_at', datetime.now(timezone.utc).isoformat()) if old.get('sha256') == digest else datetime.now(timezone.utc).isoformat(),
                history_type='actual ETF', provider='Yahoo Finance' if kind == 'prices' else 'issuer')
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')

def local_day(ts):
    return datetime.fromtimestamp(ts, ZoneInfo('Australia/Sydney')).date().isoformat()

def normalise(root, end='2026-11-16'):
    out = root / 'data/normalized'; out.mkdir(parents=True, exist_ok=True)
    audit = []
    for symbol in FUNDS:
        raw = root / 'data/raw'
        chart = json.loads((raw / f'{symbol}-prices.json').read_text())['chart']['result'][0]
        assert chart['meta']['currency'] == 'AUD'
        events = chart.get('events', {})
        splits = {local_day(v['date']): v['numerator']/v['denominator'] for v in events.get('splits', {}).values()}
        quote = chart['indicators']['quote'][0]
        prices = []; excluded_empty_dates = []; excluded_zero_volume_dates = []
        for i, ts in enumerate(chart['timestamp']):
            day = local_day(ts)
            if day > end:
                continue
            if all(quote[k][i] is None for k in ('open','high','low','close','volume')):
                excluded_empty_dates.append(day)
                continue
            if any(quote[k][i] is None for k in ('open', 'close')):
                raise ValueError(f'{symbol}: missing price on {day}')
            if quote['volume'][i] == 0:
                excluded_zero_volume_dates.append(day)
                continue
            if min(quote['open'][i],quote['close'][i]) <= 0:
                raise ValueError(f'{symbol}: nonpositive price on {day}')
            # Yahoo quotes are split-adjusted, but NOT distribution-adjusted. Undo
            # future splits to obtain as-traded prices, then process splits in engine.
            factor = 1
            for ex, ratio in splits.items():
                if ex > day: factor *= ratio
            prices.append(dict(date=day, open=quote['open'][i]*factor, close=quote['close'][i]*factor, split=splits.get(day, 1)))
        distributions = []
        if symbol in ('VAS', 'VGS'):
            items = json.loads((raw / f'{symbol}-distributions.json').read_text())['data']['items']
            for item in items:
                cash = [t for t in item['taxDetails'] if t['distributionType']['distCode'] == 'CASH']
                if not cash: raise ValueError(f'{symbol}: missing CASH distribution')
                distributions.append(dict(ex_date=item['exDividendDate'], pay_date=item['payableDate'], amount=cash[0]['distributionAmount']))
        else:
            page = (raw / f'{symbol}-distributions.html').read_text()
            fields = re.findall(r'data-api-key="Merlin API: distributions\.distributions\.(\d+)\.([^\"]+)"[^>]*>(.*?)</span>', page, re.S)
            records = {}
            for idx, key, val in fields:
                records.setdefault(idx, {})[html.unescape(key)] = html.unescape(re.sub('<[^>]+>', '', val)).strip()
            for item in records.values():
                if 'ex_date' not in item: continue
                amount = next((v for k,v in item.items() if k.startswith('distribution ')), None)
                if amount is None: raise ValueError(f'{symbol}: missing cash amount')
                distributions.append(dict(ex_date=datetime.strptime(item['ex_date'], '%d-%b-%y').date().isoformat(),
                    pay_date=datetime.strptime(item['payment_date'], '%d-%b-%y').date().isoformat(), amount=float(amount.replace('$','').replace(',',''))))
        distributions.sort(key=lambda x:x['ex_date'])
        if not distributions: raise ValueError(f'{symbol}: no issuer distributions')
        if len({r['ex_date'] for r in distributions}) != len(distributions): raise ValueError('Duplicate distributions')
        for d in distributions:
            if not d['pay_date'] or d['pay_date'] < d['ex_date']: raise ValueError('Invalid payment date')
        # Compare all Yahoo events within issuer coverage, not just matched rows.
        issuer = {d['ex_date']:float(d['amount']) for d in distributions}
        discrepancies = []
        for div in events.get('dividends', {}).values():
            day = local_day(div['date']); amount = div['amount']
            factor = 1
            for ex, ratio in splits.items():
                if ex > day: factor *= ratio
            if day >= distributions[0]['ex_date'] and (day not in issuer or abs(amount*factor-issuer[day]) > 0.001):
                discrepancies.append(dict(date=day, yahoo=amount*factor, issuer=issuer.get(day)))
        write_csv(out / f'{symbol}-prices.csv', prices)
        write_csv(out / f'{symbol}-distributions.csv', distributions)
        audit.append(dict(symbol=symbol, first_price=prices[0]['date'], last_price=prices[-1]['date'],
            price_rows=len(prices), distributions=len(distributions), splits=splits, discrepancies=discrepancies, excluded_empty_dates=excluded_empty_dates, excluded_zero_volume_dates=excluded_zero_volume_dates,
            history_type='actual ETF; no proxies', price_convention='as traded; cash distributions separate'))
    (out / 'audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    return audit

def load(root):
    prices, distributions = {}, {}
    for s in FUNDS:
        with open(root / f'data/normalized/{s}-prices.csv') as f:
            prices[s] = {r['date']: {k:float(r[k]) for k in ('open','close','split')} for r in csv.DictReader(f)}
        with open(root / f'data/normalized/{s}-distributions.csv') as f:
            distributions[s] = [dict(ex_date=r['ex_date'],pay_date=r['pay_date'],amount=float(r['amount'])) for r in csv.DictReader(f)]
    return prices, distributions
