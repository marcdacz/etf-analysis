import argparse
import json
from pathlib import Path
from .data import fetch, normalise
from .analysis import run
from .validate import validate
from .reentry import run as run_reentry
from .reentry import validate as validate_reentry


def main():
    p=argparse.ArgumentParser(description='Actual ETF history, pre-tax accumulation backtests')
    p.add_argument('command',choices=['fetch','run','all','validate','reentry','validate-reentry'])
    p.add_argument('--config',default='config.json')
    p.add_argument('--rules',default='config_reentry.json',help='Rules for the separate re-entry study')
    p.add_argument('--refresh',action='store_true',help='Explicitly replace cached source data')
    a=p.parse_args();root=Path.cwd();config=json.loads(Path(a.config).read_text())
    if a.command in ('fetch','all'):
        fetch(root,a.refresh);audit=normalise(root,config['end'])
        print(json.dumps(audit,indent=2))
    if a.command in ('run','all'):run(root,config)
    if a.command == 'validate':validate(root)
    if a.command == 'reentry':run_reentry(root,config,json.loads(Path(a.rules).read_text()))
    if a.command == 'validate-reentry':validate_reentry(root)

if __name__=='__main__':main()
