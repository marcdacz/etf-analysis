"""Build reader pages and figures from the saved results. Does not run a backtest."""
from datetime import date, timedelta
from html import escape
from pathlib import Path
import csv
import math
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'docs/assets'
PORTFOLIOS = {
    'NDQ': ('NDQ', '100% NDQ'),
    'Vanguard diversified': ('VAS / VGS', '30 / 70'),
    'Betashares diversified': ('A200 / BGBL', '30 / 70'),
    'Betashares growth tilt': ('A200 / BGBL / NDQ', '20 / 50 / 30'),
    'Global growth tilt': ('BGBL / NDQ', '70 / 30'),
}
COLORS = {'hold': '#2563eb', 'exit_15': '#b45309', 'exit_20': '#15803d',
          'exit_20_cash': '#b45309', 'exit_20_reenter_15': '#15803d',
          'peak_reentry': '#15803d', 'trend': '#7e22ce', 'contributed': '#64748b'}


def read(path):
    with (ROOT / path).open(newline='') as f:
        return list(csv.DictReader(f))


def find(rows, portfolio='NDQ', strategy='hold', window='common', **extra):
    match = dict(study='main', portfolio=portfolio, strategy=strategy,
                 window=window, cash_rate='0.0', **extra)
    found = [r for r in rows if all(r.get(k) == v for k, v in match.items())]
    if len(found) != 1:
        raise ValueError(f'Expected one saved result for {match}; found {len(found)}')
    return found[0]


def money(value):
    n = float(value)
    return ('-' if n < 0 else '') + f'${abs(n):,.0f}'


def percent(value):
    return f'{float(value):.1%}'


def signed_money(value):
    n = float(value)
    return ('+' if n >= 0 else '-') + money(abs(n))


def portfolio_label(name):
    title, ratio = PORTFOLIOS[name]
    return title if name == 'NDQ' else f'{title} ({ratio.replace(" ", "")})'


def table(headers, rows):
    lines = ['| ' + ' | '.join(headers) + ' |',
             '| ' + ' | '.join('---' for _ in headers) + ' |']
    lines += ['| ' + ' | '.join(map(str, r)) + ' |' for r in rows]
    return '\n'.join(lines)


def write(path, text):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.strip() + '\n')


def save_svg(name, elements, width=1100, height=620):
    ASSETS.mkdir(parents=True, exist_ok=True)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
           '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#172033} .muted{fill:#526174}</style>',
           f'<rect width="{width}" height="{height}" fill="#fff"/>', *elements, '</svg>']
    path = ASSETS / f'{name}.svg'
    path.write_text('\n'.join(svg) + '\n')
    renderer = shutil.which('rsvg-convert')
    if renderer:
        subprocess.run([renderer, str(path), '-o', str(path.with_suffix('.png'))], check=True)


def text(x, y, value, size=14, **attrs):
    attributes = ' '.join(f'{k.rstrip("_").replace("_", "-")}="{escape(str(v))}"' for k, v in attrs.items())
    return f'<text x="{x}" y="{y}" font-size="{size}" {attributes}>{escape(value)}</text>'


def overview_chart(rows):
    strategies = [('hold', 'Buy and hold'), ('peak_reentry', 'Sell at 20%, buy 15% below a later high'),
                  ('trend', '10-month trend')]
    items = ['<title>Final values for five portfolios from 2 April 2024 to 16 November 2026</title>',
             text(40, 34, 'Final portfolio value', 24, font_weight=700),
             text(40, 60, '2 Apr 2024 to 16 Nov 2026 | A$51,000 added | before tax | cash earns 0%', 14, class_='muted')]
    for i, (strategy, label) in enumerate(strategies):
        x = [40, 290, 745][i]
        items += [f'<rect x="{x}" y="81" width="16" height="12" rx="2" fill="{COLORS[strategy]}"/>', text(x+24, 92, label, 13)]
    x0, width, maximum = 300, 650, 85000
    for value in (0, 20000, 40000, 60000, 80000):
        x = x0 + width * value / maximum
        items += [f'<line x1="{x}" y1="115" x2="{x}" y2="545" stroke="#e2e8f0"/>',
                  text(x, 568, f'${value//1000}k', 12, text_anchor='middle')]
    contribution_x = x0 + width * 51000 / maximum
    items.append(f'<line x1="{contribution_x}" y1="115" x2="{contribution_x}" y2="545" stroke="#64748b" stroke-dasharray="5 5"/>')
    for i, name in enumerate(PORTFOLIOS):
        y = 130 + i * 84
        label, ratio = PORTFOLIOS[name]
        items += [text(40, y+22, label, 14, font_weight=700), text(40, y+42, ratio, 12)]
        for j, (strategy, _) in enumerate(strategies):
            value = float(find(rows, name, strategy, 'common_ready')['final_wealth'])
            bar_width = width * value / maximum
            bar_y = y + j * 20
            items += [f'<rect x="{x0}" y="{bar_y}" width="{bar_width:.2f}" height="14" rx="2" fill="{COLORS[strategy]}"/>',
                      text(x0+bar_width+8, bar_y+12, money(value), 12)]
    items += [text(40, 600, 'Dashed line: money added. Missing prices on two trading days may affect the results.', 12)]
    save_svg('overview', items)


def line_chart(name, title, points, strategies, labels, contributed):
    # points: list of saved daily rows from one account window.
    chosen = {s: [p for p in points if p['strategy'] == s] for s in strategies}
    dates = [date.fromisoformat(p['date']) for p in chosen[strategies[0]]]
    start, end = dates[0], dates[-1]
    values = [float(p['wealth']) for rows in chosen.values() for p in rows]
    high = math.ceil(max(values + [contributed]) / 10000) * 10000
    left, top, width, height = 88, 116, 930, 330
    total_days = max(1, (end-start).days)
    items = [f'<title>{escape(title)}</title>', text(40, 34, title, 23, font_weight=700),
             text(40, 60, f'{start:%d %b %Y} to {end:%d %b %Y} | {money(contributed)} added | AUD, before tax | cash earns 0%', 14)]
    for i in range(6):
        value = high*i/5; y = top+height-value/high*height
        items += [f'<line x1="{left}" y1="{y}" x2="{left+width}" y2="{y}" stroke="#e2e8f0"/>',
                  text(left-12, y+4, f'${value/1000:,.0f}k', 12, text_anchor='end')]
    for i in range(5):
        d = start + timedelta(days=round(total_days*i/4))
        x = left+width*i/4
        items.append(text(x, top+height+28, d.strftime('%b %Y'), 12, text_anchor='middle'))
    for strategy in strategies:
        coords = ' '.join(f'{left+(date.fromisoformat(p["date"])-start).days/total_days*width:.2f},{top+height-float(p["wealth"])/high*height:.2f}' for p in chosen[strategy])
        items.append(f'<polyline points="{coords}" fill="none" stroke="{COLORS[strategy]}" stroke-width="2.5"/>')
    contribution_points = ' '.join(f'{left+(date.fromisoformat(p["date"])-start).days/total_days*width:.2f},{top+height-float(p["contributed"])/high*height:.2f}' for p in chosen[strategies[0]])
    items.append(f'<polyline points="{contribution_points}" fill="none" stroke="{COLORS["contributed"]}" stroke-width="1.5" stroke-dasharray="5 5"/>')
    legend = [(s, labels[s]) for s in strategies] + [('contributed', 'Money added')]
    for i, (strategy, label) in enumerate(legend):
        x = 88 + (i % 2)*470; y = 514+(i//2)*26
        dash = ' stroke-dasharray="5 5"' if strategy == 'contributed' else ''
        items += [f'<line x1="{x}" y1="{y}" x2="{x+28}" y2="{y}" stroke="{COLORS[strategy]}" stroke-width="3"{dash}/>',
                  text(x+40, y+4, label, 14)]
    items.append(text(40, 590, 'Values include trading costs. Missing prices on two trading days may affect the results.', 12))
    save_svg(name, items)


NAV = '[Overview](../../README.md) · [How the tests work](../methodology.md) · [Run the project](../running.md)'
CAUTION = '**Keep in mind:** two missing trading days may change signals, trade dates and the biggest recorded fall. Results are before tax. They do not tell us what markets will do next.'


def main():
    original = read('results/trials.csv')
    reentry = read('results/reentry/trials.csv')
    tactical = read('results/tactical/trials.csv')
    overview_chart(tactical)
    charts = [
        ('exit-targets-ndq', 'NDQ: take profits or keep holding?', read('results/common_daily.csv'),
         ['hold', 'exit_15', 'exit_20'], {'hold': 'Buy and hold', 'exit_15': 'Sell at 15%, stay in cash', 'exit_20': 'Sell at 20%, stay in cash'}, 62000),
        ('fixed-reentry-ndq', 'NDQ: waiting for 15% below the sale value', read('results/reentry/common_daily.csv'),
         ['hold', 'exit_20_cash', 'exit_20_reenter_15'], {'hold': 'Buy and hold', 'exit_20_cash': 'Sell at 20%, stay in cash', 'exit_20_reenter_15': 'Sell at 20%, wait for a 15% drop'}, 62000),
    ]
    tactical_daily = read('results/tactical/common_daily.csv')
    for asset, title, strategy, label in [
        ('peak-reentry-ndq', 'NDQ: buying after a fall from the later high', 'peak_reentry', 'Sell at 20%, buy after a 15% peak drop'),
        ('trend-ndq', 'NDQ: a 10-month trend rule', 'trend', '10-month trend')]:
        charts.append((asset, title, [p for p in tactical_daily if p['window']=='common_ready'],
                       ['hold', strategy], {'hold': 'Buy and hold', strategy: label}, 51000))
    for asset, title, points, strategies, labels, added in charts:
        line_chart(asset, title, [p for p in points if p['portfolio']=='NDQ'], strategies, labels, added)

    wealth_rows = []
    for name in PORTFOLIOS:
        wealth_rows.append([portfolio_label(name), *[money(find(tactical, name, s, 'common_ready')['final_wealth']) for s in ('hold','peak_reentry','trend')]])
    main_table = table(['Portfolio (weights %)', 'Hold', '20% exit / 15% peak drop', '10-month trend'], wealth_rows)
    write('README.md', f'''
# ETF backtests

> **The takeaway:** holding finished ahead in most comparisons. Taking profits and buying a dip sometimes helped, but we did not find a trading rule that won across both periods and all five portfolios.

We compared regular ETF investing with profit targets, dip-buying rules and a simple trend rule. Each strategy gets the same money, pays trading costs and uses actual ETF history.

- **Holding finished ahead in all five portfolios from May 2023, and four of five from April 2024.**
- **Buying 15% below the sale value left all five May 2023 accounts waiting in cash.** Other starting dates did lead to buying back.
- **Buying 15% below a later high helped NDQ in the April 2024 test.** It finished behind holding from May 2023, so the starting date matters.
- **The 10-month trend rule finished with less money than holding in both shared periods.** It reduced the biggest falls in some portfolios.

## A quick look at the results

**2 April 2024 to 16 November 2026.** This start gives every portfolio enough history for the trend rule. Each account starts with **A$20,000**, adds **A$1,000 a month** and receives **A$51,000 in total**. Cash earns 0%.

![Final values for all five portfolios, comparing holding, peak-based re-entry and the 10-month trend rule](docs/assets/overview.png)

{main_table}

All amounts are AUD and include the money added. Values include trading costs and estimated selling costs at the end. Tax is excluded. These accounts start fresh in April 2024; earlier gains are not carried forward.

**There are trade-offs.** NDQ's peak-drop rule ended at **$76,323**, with a biggest recorded fall of **10.9%**, versus **$65,879** and **21.4%** for holding. From May 2023, that rule ended at **$91,234**, below holding's **$96,362**. One good starting date is not enough to call it a better strategy.

## Read each backtest

| Backtest | What we learned |
| --- | --- |
| [1. Sell at 15% or 20%, then stay in cash](docs/01-profit-targets/README.md) | Less time in shares meant less money at the end of the May 2023 comparison. |
| [2. Buy back 15% below the sale value](docs/02-fixed-reentry/README.md) | The price rule could leave an account in cash for years. |
| [3. Buy after a 15% fall from the later high](docs/03-peak-reentry/README.md) | More chances to buy back, with results that changed by portfolio and start date. |
| [4. Follow the 10-month trend](docs/04-monthly-trend/README.md) | Some smaller falls, but less money at the end in both shared periods. |

**These results have limits.** Prices are missing for two trading days, which may affect trades and reported losses. Some ETFs have short histories. The tests are before tax and do not tell us what will happen next. [See the assumptions and data limits](docs/methodology.md).

## Run it yourself

Python 3.10+ and `curl` are enough. The saved data is included, so these commands work offline:

```sh
python3 -m unittest discover -s tests -v
python3 -m etf_backtest tactical
python3 -m etf_backtest validate-tactical
```

[Setup, all run commands and outputs](docs/running.md) · [How the tests work](docs/methodology.md)

The saved checks passed **39 tests** and checked **33,940 scenarios** in the latest comparison. The earlier two studies each contain 20,316 scenarios. These studies reuse accounts and periods, so those counts are not independent pieces of evidence.
''')

    first_table = table(['Portfolio', 'Hold', 'Sell at 15%', 'Sell at 20%'],
        [[portfolio_label(n), *[money(find(original,n,s)['final_wealth']) for s in ('hold','exit_15','exit_20')]] for n in PORTFOLIOS])
    first_detail = []
    for strategy,label in [('hold','Hold'),('exit_15','Sell at 15%'),('exit_20','Sell at 20%')]:
        r=find(original,strategy=strategy)
        first_detail.append([label,money(r['final_wealth']),money(r['profit']),percent(r['money_weighted_return']),percent(r['maximum_drawdown']),r['time_to_target_days'] or 'Not used',r['exit_date'] or 'No sale'])
    stress_rows = []
    for name in ('NDQ', 'Vanguard diversified'):
        r = find(original, name, 'exit_20', '12m', start='2022-01-04')
        assert r['never_reached_target'] == '1'
        stress_rows.append([portfolio_label(name), money(r['contributed_capital']), money(r['final_wealth']),
                            money(r['profit']), percent(r['maximum_drawdown']), r['completed_exits']])
    write('docs/01-profit-targets/README.md', f'''
# 1. Take profits, then stay in cash

> **TL;DR:** holding ended with more money than either profit target in all five portfolios in the May 2023 comparison. Selling avoided later price swings, but the accounts missed later gains.

{NAV}

## What we tested

Start on **12 May 2023** and finish on **16 November 2026**. Each account starts with A$20,000 and adds A$1,000 a month from the following month, for **A$62,000 added in total**. Cash earns 0%.

| Rule | What happens after selling? |
| --- | --- |
| Buy and hold | Keep investing. There is no profit target. |
| Sell at a 15% gain | Sell everything, then keep the proceeds and later deposits in cash. |
| Sell at a 20% gain | The same, with a higher target. |

A gain is measured against the money added to the account. New deposits are capital, not profit. Signals use the closing price; sales happen at the next available open. A price gap can leave the actual sale below the target.

## What happened

![NDQ account values for holding and selling at 15% or 20%, with money added shown separately](../assets/exit-targets-ndq.png)

{first_table}

Values are AUD, before tax, after trading costs and estimated selling costs at the end. [Portfolio weights](../methodology.md#portfolios) are the same in every study.

### NDQ in more detail

{table(['Rule','Final value','Profit','Annual return*','Biggest fall*','Days to target','Sale date'],first_detail)}

*Annual return means the money-weighted return, which accounts for the dates of deposits. Biggest fall means the largest fall in the account's value after adjusting for deposits. These are historical results, not loss limits.*

## What to take from this

The lower target took money out of shares sooner. The higher target stayed invested longer. Both missed later gains on this market path. A profit target also does nothing to protect against a fall **before** the account reaches that target.

This is one shared period, not a rule for every market. The saved results also test annual starts, monthly 3, 6, 12 and 24-month periods, and quarterly 3 and 5-year periods where actual ETF history exists.

### What if the target never arrives?

These separate accounts ran from **4 January to 30 December 2022**. Neither reached the 20% target. They stayed invested through the losses.

{table(['Portfolio','Money added','Final value','Profit','Biggest fall','Sales'],stress_rows)}

A take-profit rule is not a stop-loss rule.

{CAUTION}

## Check the details

[Full saved report](../../results/report.md) · [Every account and metric](../../results/trials.csv) · [Other start dates](../../results/summary.csv) · [Trade log](../../results/trade_ledger.csv) · [Validation](../../results/validation.json)

To repeat this study:

```sh
python3 -m etf_backtest run
python3 -m etf_backtest validate
```

[Next: buying back below the sale value](../02-fixed-reentry/README.md)
''')

    fixed_table=[]
    for n in PORTFOLIOS:
        hold=find(reentry,n,'hold');r=find(reentry,n,'exit_20_reenter_15')
        fixed_table.append([portfolio_label(n),money(hold['final_wealth']),money(r['final_wealth']),r['completed_exits'],r['completed_reentries'],r['waiting_days']])
    examples=[]
    for s,label in [('hold','Hold'),('exit_20_cash','Sell, stay in cash'),('exit_20_reenter_15','Sell, buy below sale')]:
        r=find(reentry,strategy=s,window='24m',start='2018-01-02')
        examples.append([label,money(r['final_wealth']),percent(r['money_weighted_return']),percent(r['maximum_drawdown']),r['completed_exits'],r['completed_reentries']])
    cycles=read('results/reentry/cycles.csv')
    chosen=[r for r in cycles if r['study']=='main' and r['portfolio']=='NDQ' and r['window']=='24m' and r['trial_start']=='2018-01-02' and r['cash_rate']=='0.0']
    cycle_table=table(['Round','Bought','Sold','Bought back','Days waiting'],[[r['cycle'],r['entry_date'],r['exit_date'] or 'Not sold',r['reentry_date'] or 'Still waiting',r['wait_days']] for r in chosen])
    write('docs/02-fixed-reentry/README.md', f'''
# 2. Buy back below the sale value

> **TL;DR:** none of the five accounts starting in May 2023 bought back in. Their reference baskets never fell 15% below the sale value. Some other starting dates did lead to buying back, so this was not true of the whole history.

{NAV}

## The rule

```mermaid
flowchart LR
    A[Invest and add money monthly] --> B[Gain reaches 20%]
    B --> C[Sell at the next open]
    C --> D[Wait in cash]
    D --> E[Basket closes 15% below sale value]
    E --> F[Buy at the next open]
    F --> A
```

We track the same units that were sold, including later distributions and split changes. Deposits into the real cash account do not move the reference. When buying back, invest the available cash and reset the next 20% target to that account value.

**Simple example, ignoring costs and distributions:** buy at 100, sell at 120, then wait for 102. If the market rises to 160 and falls to 136, it is down 15% from the high but still does not meet this rule.

## The May 2023 accounts stayed in cash

**12 May 2023 to 16 November 2026. A$62,000 added per account. Cash earns 0%.**

![NDQ values for holding, selling permanently and waiting for 15% below the sale value](../assets/fixed-reentry-ndq.png)

*The two selling lines overlap because this NDQ account never bought back.*

{table(['Portfolio','Hold','Buy below sale','Sales','Times bought back','Days still waiting'],fixed_table)}

Values are AUD, before tax, after trading costs and estimated selling costs at the end.

## A different start did lead to buying back

For **NDQ from 2 January 2018 to 31 December 2019**, each account received **A$43,000**. This is a separate account and period, not a continuation of the May 2023 test.

{table(['Rule','Final value','Annual return*','Biggest fall*','Sales','Times bought back'],examples)}

The account using this rule traded as follows:

{cycle_table}

Buying back left more money than staying in cash in this example. It still finished a little behind holding. The annual return accounts for deposit dates; the biggest fall is adjusted for deposits.

## What to take from this

A fixed sale price can leave you waiting for years. A large fall from a later high may still be above the price you sold at. Buying back also puts the money at risk again; a 15% drop does not mean the decline is over.

{CAUTION}

## Check the details

[Full saved report](../../results/reentry/report.md) · [Every account](../../results/reentry/trials.csv) · [Each round of buying and selling](../../results/reentry/cycles.csv) · [Trade log](../../results/reentry/trade_ledger.csv) · [Validation](../../results/reentry/independent_validation.json)

```sh
python3 -m etf_backtest reentry
python3 -m etf_backtest validate-reentry
```

[Next: measuring the drop from the later high](../03-peak-reentry/README.md)
''')

    peak_table=[]
    for n in PORTFOLIOS:
        h=find(tactical,n,'hold','common_ready');r=find(tactical,n,'peak_reentry','common_ready')
        peak_table.append([portfolio_label(n),money(h['final_wealth']),money(r['final_wealth']),percent(h['maximum_drawdown']),percent(r['maximum_drawdown']),r['completed_reentries']])
    sensitivity=[]
    for window in ('common','common_ready'):
        h=find(tactical,strategy='hold',window=window);r=find(tactical,strategy='peak_reentry',window=window)
        sensitivity.append([h['start'],money(h['contributed_capital']),money(h['final_wealth']),money(r['final_wealth']),signed_money(r['wealth_minus_hold'])])
    ndq_peak=[]
    for s,label in [('hold','Hold'),('fixed_reentry','15% below sale'),('peak_reentry','15% below later high')]:
        r=find(tactical,strategy=s,window='common_ready')
        ndq_peak.append([label,money(r['profit']),percent(r['money_weighted_return']),percent(r['maximum_drawdown']),r['completed_exits'],r['completed_reentries'],r['cash_days']])
    write('docs/03-peak-reentry/README.md', f'''
# 3. Buy after a fall from the later high

> **TL;DR:** this rule gave NDQ more chances to buy back. It ended ahead of holding from April 2024, but behind holding from May 2023. It did not beat holding across all five portfolios.

{NAV}

## What changed?

Keep the 20% profit target. After selling, follow the highest **closing** value reached by the sold basket. Buy back after a 15% fall from that high. The next 20% target resets after buying.

```mermaid
flowchart LR
    A[Sell after a 20% gain] --> B[Track the highest closing basket value]
    B --> C[Basket closes 15% below that high]
    C --> D[Buy at the next open]
    D --> E[Reset the gain target]
    E --> A
```

**Example, ignoring costs and distributions:** sell at 120, watch the basket rise to 160, then buy after it closes at 136 or below. That is a higher price than the sale. The rule buys a fall from the later high; it does not promise a cheaper price than you sold at.

The peak starts at the exit day's close. Later distributions and split changes are included in the reference basket. Its distributions are only used for the signal and are never added to the real cash account.

## Results once all portfolios had enough trend history

**2 April 2024 to 16 November 2026. A$51,000 added per account. Cash earns 0%.** This is the same start used to compare the trend strategy.

![NDQ values for holding and buying after a 15% fall from the later high](../assets/peak-reentry-ndq.png)

{table(['Portfolio','Hold','Peak-drop rule','Hold: biggest fall','Rule: biggest fall','Times bought back'],peak_table)}

Values are AUD, before tax, after trading costs and estimated selling costs at the end. The biggest fall is adjusted for deposits, and is not a limit on future losses.

### NDQ's result changed with the starting date

Both tests finish on 16 November 2026. Each starts fresh with A$20,000 and then adds A$1,000 a month. Do not compare the raw balances across rows without accounting for the different dates and deposits.

{table(['Start','Money added','Hold','Peak-drop rule','Rule minus hold'],sensitivity)}

### NDQ from April 2024, in more detail

{table(['Rule','Profit','Annual return*','Biggest fall','Sales','Times bought back','Days in cash'],ndq_peak)}

*Annual return is money-weighted, so it accounts for when deposits were made.*

## What to take from this

The later-high rule solved one problem with the fixed-sale rule: it allowed buying back even after prices had moved above the old sale value. It also brought new risks. You can pay more than you sold for, buy before a decline is over, or miss gains while waiting.

The 20% target still offers no protection before it is reached. In this test, NDQ was the only April 2024 portfolio where this rule finished ahead of holding. That is worth studying further, but it is not enough to call the rule a rule we can rely on.

{CAUTION}

## Check the details

[Full saved comparison](../../results/tactical/report.md) · [Every account](../../results/tactical/trials.csv) · [Trade log](../../results/tactical/trade_ledger.csv) · [Buying and selling rounds](../../results/tactical/cycles.csv) · [Validation](../../results/tactical/independent_validation.json)

```sh
python3 -m etf_backtest tactical
python3 -m etf_backtest validate-tactical
```

[Next: the 10-month trend rule](../04-monthly-trend/README.md)
''')

    trend_table=[]
    for n in PORTFOLIOS:
        h=find(tactical,n,'hold','common_ready');r=find(tactical,n,'trend','common_ready')
        trend_table.append([portfolio_label(n),money(h['final_wealth']),money(r['final_wealth']),percent(h['maximum_drawdown']),percent(r['maximum_drawdown']),r['completed_exits']])
    warmup=[]
    for n in PORTFOLIOS:
        r=find(tactical,n,'trend','common')
        warmup.append([portfolio_label(n),r['trend_ready_date'],r['trend_warmup_cash_days']])
    trend_ndq=[]
    for s,label in [('hold','Hold'),('trend','10-month trend')]:
        r=find(tactical,strategy=s,window='common_ready')
        trend_ndq.append([label,money(r['profit']),percent(r['money_weighted_return']),percent(r['maximum_drawdown']),r['completed_entries'],r['completed_exits'],r['cash_days']])
    write('docs/04-monthly-trend/README.md', f'''
# 4. Follow the 10-month trend

> **TL;DR:** this rule ended with less money than holding in all five portfolios in both shared periods. It reduced the biggest falls in some portfolios, but it could also sell late and miss part of a recovery.

{NAV}

## The rule

At each completed month-end, compare a portfolio index with its average over the last ten month-ends.

```mermaid
flowchart LR
    A[Month ends] --> B{{Index above its 10-month average?}}
    B -->|Yes| C[Hold ETFs]
    B -->|No or equal| D[Hold cash]
    C --> E[Make any change at the next open]
    D --> E
```

There is **no 20% profit target** here. The account can keep holding through a long rise. Deposits continue in cash when it is out of shares.

The index is built from actual ETF returns, including distributions and split changes. It is reset to the target weights each month. It is a signal, not the value of the real account. The real account still pays costs, buys whole units and receives distributions on their payment dates. [How the signal is built](../methodology.md#the-trend-signal).

## Compare accounts with enough starting history

**2 April 2024 to 16 November 2026. A$51,000 added per account. Cash earns 0%.**

![NDQ account values for holding and following the 10-month trend rule](../assets/trend-ndq.png)

{table(['Portfolio','Hold','10-month trend','Hold: biggest fall','Trend: biggest fall','Sales'],trend_table)}

Values are AUD, before tax, after trading costs and estimated selling costs at the end. The biggest fall is adjusted for deposits.

### NDQ in more detail

{table(['Rule','Profit','Annual return*','Biggest fall','Times invested','Sales','Days in cash'],trend_ndq)}

*Annual return accounts for the dates of deposits. Times invested includes the first purchase; times bought back does not.*

## Why we also use a later start

The original comparison starts on **12 May 2023**. Funds using BGBL did not have ten complete monthly observations yet, so the trend accounts waited in cash. We did not invent earlier ETF prices to fill the gap.

{table(['Portfolio','First date with enough signal history','Days waiting for history from May 2023'],warmup)}

The April 2024 comparison starts every account fresh after all five portfolios have enough history. It does not carry earlier gains forward. Both starts are in the saved results, and the trend rule finished below holding in each.

A missing VGS quote on 31 December 2014 also removes that month-end from the earlier signal history. The lookback restarts after that gap. [Data limits](../methodology.md#missing-data).

## What to take from this

A monthly signal reacts after a move has happened. During a sharp fall it can sell late; during a fast recovery it can buy back late. Sideways markets can lead to repeated changes and extra costs.

Smaller losses can still be useful, even with a lower ending balance. Here, that benefit varied by portfolio. The results do not make a case that this exact rule is a better overall choice than holding.

These are simple research rules. They do not copy a named fund manager's strategy.

{CAUTION}

## Check the details

[Full saved comparison](../../results/tactical/report.md) · [Every account](../../results/tactical/trials.csv) · [Month-end signals](../../results/tactical/trend_history.csv) · [Other start dates](../../results/tactical/summary.csv) · [Validation](../../results/tactical/independent_validation.json)

```sh
python3 -m etf_backtest tactical
python3 -m etf_backtest validate-tactical
```

[Back to the overview](../../README.md)
''')
    print('Built the main README, four study READMEs and five figures from saved CSVs.')
    if not shutil.which('rsvg-convert'):
        print('PNG export skipped. Install librsvg and run this script again to refresh PNGs.')


if __name__ == '__main__':
    main()
