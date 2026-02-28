from __future__ import annotations

import os
import sqlite3
from typing import Optional


def _default_db_path() -> str:
    # Dashboard Prisma SQLite DB
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, ".."))
    return os.path.join(repo_root, "dashboard", "prisma", "dev.db")


def iv_percentile(
    *,
    symbol: str,
    current_iv: float,
    lookback: int = 252,
    db_path: str | None = None,
) -> Optional[float]:
    """Compute percentile rank of current_iv vs last `lookback` IV observations for symbol.

    Returns percentile in [0, 100]. If insufficient history, returns None.

    Percentile definition (simple empirical CDF):
      pct = 100 * (#history values <= current_iv) / n
    """

    if not symbol or current_iv is None:
        return None

    db_path = db_path or os.getenv("IV_DB_PATH") or _default_db_path()
    if not os.path.exists(db_path):
        return None

    sym = symbol.strip().upper()

    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        # Table name as created by Prisma for model IvDaily: "IvDaily"
        # Columns: symbol, date, iv, ...
        cur.execute(
            'SELECT iv FROM "IvDaily" WHERE symbol=? ORDER BY date DESC LIMIT ?',
            (sym, int(lookback)),
        )
        rows = cur.fetchall()
    except Exception:
        return None
    finally:
        try:
            con.close()
        except Exception:
            pass

    vals = []
    for (v,) in rows:
        try:
            fv = float(v)
            if fv > 0:
                vals.append(fv)
        except Exception:
            continue

    n = len(vals)
    if n < 30:
        return None

    le = sum(1 for x in vals if x <= float(current_iv))
    return (le / n) * 100.0
