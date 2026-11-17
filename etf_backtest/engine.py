"""Event-driven long-only accounting. Signals at close, fills next open."""
from datetime import date, timedelta
import math


def add_months(day, months):
    d = date.fromisoformat(day); m = d.year*12 + d.month-1+months
    return date(m//12,m%12+1,1).isoformat()


def xirr(flows):
    """Unique root for contributions only and one positive terminal value."""
    origin = flows[0][0]
    if flows[-1][0] <= origin or flows[-1][1] <= 0: return None
    def npv(log_growth):
        return sum(v*math.exp(-log_growth*(d-origin).days/365.25) for d,v in flows)
    lo, hi = -30., 30.
    if npv(lo)*npv(hi)>0: return None
    for _ in range(100):
        mid=(lo+hi)/2
        if npv(mid)>0:lo=mid
        else:hi=mid
    return math.expm1((lo+hi)/2)


def simulate(prices, distributions, weights, start, end, config, threshold=None, cash_rate=0):
    symbols=list(weights)
    calendars=[{d for d in prices[s] if start<=d<=end} for s in symbols]
    if not calendars[0] or any(c != calendars[0] for c in calendars[1:]):
        raise ValueError('Missing or unequal trading calendars; no silent forward fill')
    days=sorted(calendars[0]); first=days[0]
    units={s:0 for s in symbols}; cash=0.; contributed=0.; receivables=[]
    flows=[]; ledger=[]; path=[]; pending=False; exited=False
    signal=None; exit_day=None; total_fees=0.; total_slippage=0.; total_distributions=0.; interest_total=0.
    index=1.; peak=1.; maxdd=0.; prev_wealth=None; prev_day=date.fromisoformat(first)
    ex_events={}
    for s in symbols:
        for div in distributions[s]:ex_events.setdefault(div['ex_date'],[]).append((s,div))
    def liquidation(field, day):
        return cash+sum(v for _,v in receivables)+sum(max(0.,units[s]*prices[s][day][field]*(1-config['slippage'])-config['brokerage']) for s in symbols if units[s])
    for day in days:
        current=date.fromisoformat(day)
        # Accrue actual calendar days. Payments enter cash on their actual dates,
        # including non-trading days; no interest on unpaid receivables.
        cursor=prev_day
        while cursor<current:
            cursor+=timedelta(days=1)
            earned=cash*((1+cash_rate)**(1/365.25)-1);cash+=earned;interest_total+=earned
            for pay,amount in list(receivables):
                if pay<=cursor.isoformat():
                    cash+=amount;receivables.remove((pay,amount))
                    ledger.append(dict(date=cursor.isoformat(),event='distribution_payment',symbol='',units=0,price=0,amount=amount))
        external=config['initial_capital'] if day==first else 0
        if day!=first and day[:7]!=prev_day.isoformat()[:7]:external+=config['monthly_contribution']
        if external:
            cash+=external;contributed+=external;flows.append((current,-external))
            ledger.append(dict(date=day,event='contribution',symbol='',units=0,price=0,amount=external))
        # Entitlement belongs to holders BEFORE ex-date opening trades.
        for s in symbols:
            ratio=prices[s][day]['split']
            if ratio!=1:
                units[s]*=ratio
                ledger.append(dict(date=day,event='split',symbol=s,units=units[s],price=0,amount=ratio))
        for s,div in ex_events.get(day,[]):
            amount=units[s]*div['amount']
            if amount:
                total_distributions+=amount
                receivables.append((div['pay_date'],amount))
                ledger.append(dict(date=day,event='distribution_entitlement',symbol=s,units=units[s],price=div['amount'],amount=amount))
        for pay,amount in list(receivables):
            if pay<=day:
                cash+=amount;receivables.remove((pay,amount))
                ledger.append(dict(date=day,event='distribution_payment',symbol='',units=0,price=0,amount=amount))
        if pending:
            for s in symbols:
                if not units[s]:continue
                px=prices[s][day]['open']*(1-config['slippage']); gross=units[s]*px
                cash+=gross-config['brokerage']; total_fees+=config['brokerage']
                total_slippage+=units[s]*prices[s][day]['open']*config['slippage']
                ledger.append(dict(date=day,event='sell',symbol=s,units=units[s],price=px,amount=gross-config['brokerage']))
                units[s]=0
            exited=True;pending=False;exit_day=day
        scheduled=day==first or day[:7]!=prev_day.isoformat()[:7]
        if scheduled and not exited:
            total=cash+sum(units[s]*prices[s][day]['open'] for s in symbols)
            deficits={s:max(0,weights[s]*total-units[s]*prices[s][day]['open']) for s in symbols}
            deficit_sum=sum(deficits.values()); available=cash
            # Fixed cash budgets prevent symbol-order bias; residual cash remains.
            for s in symbols:
                budget=min(available,available*deficits[s]/deficit_sum) if deficit_sum else 0
                px=prices[s][day]['open']*(1+config['slippage'])
                qty=max(0,math.floor((budget-config['brokerage'])/px))
                if qty:
                    cost=qty*px+config['brokerage'];cash-=cost;units[s]+=qty;total_fees+=config['brokerage']
                    total_slippage+=qty*prices[s][day]['open']*config['slippage']
                    ledger.append(dict(date=day,event='buy',symbol=s,units=qty,price=px,amount=-cost))
        wealth=liquidation('close',day)
        if prev_wealth is None:index=wealth/contributed
        else:index*=wealth/(prev_wealth+external)
        peak=max(peak,index);maxdd=min(maxdd,index/peak-1)
        gain=wealth/contributed-1
        if threshold is not None and not exited and not pending and gain+1e-12>=threshold:
            signal=day;pending=True
            ledger.append(dict(date=day,event='exit_signal',symbol='',units=0,price=0,amount=gain))
        if cash < -1e-6:raise AssertionError('Negative cash')
        path.append(dict(date=day,wealth=wealth,contributed=contributed,cash=cash,receivables=sum(v for _,v in receivables),gain=gain,return_index=index))
        prev_wealth=wealth;prev_day=current
    flows.append((date.fromisoformat(days[-1]),wealth))
    return dict(start=first,end=days[-1],final_wealth=wealth,contributed_capital=contributed,profit=wealth-contributed,
        money_weighted_return=xirr(flows),maximum_drawdown=maxdd,signal_date=signal or '',exit_date=exit_day or '',
        time_to_target_days=(date.fromisoformat(signal)-date.fromisoformat(first)).days if signal else '',
        completed_exits=int(exited),never_reached_target=int(threshold is not None and signal is None),
        pending_exit=int(pending),brokerage_paid=total_fees,slippage_paid=total_slippage,
        distribution_entitlements=total_distributions,cash_interest=interest_total,final_cash=cash,
        final_receivables=sum(v for _,v in receivables)),path,ledger
