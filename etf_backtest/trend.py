"""Causal month-end signals constructed solely from actual ETF total returns."""
from calendar import monthrange
from datetime import date, timedelta
import statistics


def last_weekday(month):
    year,number=map(int,month.split('-'))
    day=date(year,number,monthrange(year,number)[1])
    while day.weekday()>4:day-=timedelta(days=1)
    return day.isoformat()


def build_signals(prices, distributions, weights, lookback=10):
    if not isinstance(lookback,int) or lookback<2:
        raise ValueError('Moving average requires at least two month-end observations')
    earliest=max(min(prices[s]) for s in weights)
    latest=min(max(prices[s]) for s in weights)
    calendars=[{d for d in prices[s] if earliest<=d<=latest} for s in weights]
    # Other cached ETFs establish that a session existed even when this
    # portfolio has no quote (e.g. VGS alone on 31 December 2014).
    expected_days=sorted(set().union(*({d for d in p if earliest<=d<=latest} for p in prices.values())))
    days=sorted(set.intersection(*calendars))
    missing=sorted(set(expected_days)-set(days))
    for s in weights:
        if any(r['ex_date'] in missing for r in distributions[s]):
            raise ValueError('Missing signal quote on distribution ex-date')
        if any(prices[s].get(d,{}).get('split',1)!=1 for d in missing):
            raise ValueError('Missing signal quote on split date')
    last_by_month={d[:7]:d for d in expected_days}
    # Exclude the inception stub. The final cached month may be incomplete.
    month_ends={d for m,d in last_by_month.items() if d in days and m!=days[0][:7] and
                (m<days[-1][:7] or d==last_weekday(m))}
    divs={s:{r['ex_date']:r['amount'] for r in distributions[s]} for s in weights}
    components={s:100*weights[s] for s in weights}
    closes=[];signals={};history=[]
    previous=None
    for day in days:
        if previous and day[:7]!=previous[:7] and last_by_month[previous[:7]] in missing:
            # A missing closing observation cannot become a synthetic month end.
            # Restart the consecutive-month warm-up and skip that rebalance.
            closes=[]
            history.append(dict(date=last_by_month[previous[:7]],total_return_index='',moving_average='',
                                desired_invested='',observations=0,status='missing month-end quote; warm-up reset',
                                history_type='missing data; no value imputed'))
        if previous is not None:
            for s in weights:
                q=prices[s][day]
                # Price convention is as-traded: split ratio applies to both
                # the closing price and post-split per-unit distribution.
                components[s]*=q['split']*(q['close']+divs[s].get(day,0))/prices[s][previous]['close']
        value=sum(components.values())
        if day in month_ends:
            closes.append(value)
            average=statistics.mean(closes[-lookback:]) if len(closes)>=lookback else None
            desired=value>average if average is not None else None
            if desired is not None:signals[day]=desired
            history.append(dict(date=day,total_return_index=value,moving_average=average if average is not None else '',
                                desired_invested=int(desired) if desired is not None else '',observations=len(closes),
                                status='observed month-end',
                                history_type='constructed signal index from actual ETFs; no pre-inception proxy'))
        # Rebalance the SIGNAL index at every observed month-end, including
        # inception. The actual account retains its separate trading rules.
        if day==last_by_month[day[:7]]:
            components={s:value*weights[s] for s in weights}
        previous=day
    ready=next((d for d in days if signals and d>min(signals)),None)
    return signals,history,ready
