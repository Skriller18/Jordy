#!/usr/bin/env python3

"""Capture near-term ATM IV for an underlying using Groww option chain.

Outputs a single JSON object on stdout:
  {symbol, date, iv, expiry_date, underlying_ltp, atm_strike, records}

Requires Groww auth configured in Jordy env (.env).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

# Ensure repo root is on sys.path so `import app...` works when run as a script.
HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.fo.expiry import candidate_expiries
from app.fo.groww_chain import summarize_groww_chain
from app.fo.groww_client import GrowwFoClient


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="ADANIENT", help="Underlying symbol, e.g. ADANIENT")
    ap.add_argument("--exchange", default="NSE")
    ap.add_argument("--asof", default=None, help="As-of date YYYY-MM-DD (defaults to today)")
    args = ap.parse_args()

    sym = args.symbol.strip().upper()

    asof = dt.date.today() if not args.asof else dt.date.fromisoformat(args.asof)

    groww = GrowwFoClient()

    chosen_exp = None
    chosen_metrics = None

    for exp in candidate_expiries(asof):
        try:
            oc = groww.get_option_chain(args.exchange, sym, exp)
            strikes = oc.get("strikes")
            if isinstance(strikes, dict) and len(strikes) > 0:
                chosen_exp = exp
                chosen_metrics = summarize_groww_chain(oc)
                break
        except Exception:
            continue

    out = {
        "symbol": sym,
        "date": asof.isoformat(),
        "expiry_date": chosen_exp,
    }

    if chosen_metrics:
        out.update(
            {
                "iv": chosen_metrics.get("atm_iv"),
                "underlying_ltp": chosen_metrics.get("underlying"),
                "atm_strike": chosen_metrics.get("atm_strike"),
                "records": chosen_metrics.get("records"),
            }
        )

    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
