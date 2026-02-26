from __future__ import annotations

import datetime as _dt
from typing import Iterable, List


def _last_weekday_of_month(year: int, month: int, weekday: int) -> _dt.date:
    """Return the last given weekday (0=Mon..6=Sun) in a month."""
    # start from last day of month
    if month == 12:
        d = _dt.date(year + 1, 1, 1) - _dt.timedelta(days=1)
    else:
        d = _dt.date(year, month + 1, 1) - _dt.timedelta(days=1)
    while d.weekday() != weekday:
        d -= _dt.timedelta(days=1)
    return d


def candidate_expiries(today: _dt.date | None = None) -> List[str]:
    """Generate a short list of likely expiry dates.

    Groww option-chain appears to accept only specific expiries (and may not align
    with standard Thursday expiries). We therefore try a mix:
      - next N Thursdays (weekly-like)
      - last Thursday of next few months (monthly-like)
      - last Monday of next few months (observed working for 2026-03-30)

    Returns YYYY-MM-DD strings, unique, in priority order.
    """

    if today is None:
        today = _dt.date.today()

    out: List[_dt.date] = []

    # Next 10 Thursdays
    d = today
    for _ in range(120):
        d += _dt.timedelta(days=1)
        if d.weekday() == 3:  # Thu
            out.append(d)
            if len([x for x in out if x.weekday() == 3]) >= 10:
                break

    # Last Thu + last Mon of next 6 months
    y, m = today.year, today.month
    for i in range(0, 6):
        mm = m + i
        yy = y + (mm - 1) // 12
        mo = ((mm - 1) % 12) + 1
        out.append(_last_weekday_of_month(yy, mo, 3))  # Thu
        out.append(_last_weekday_of_month(yy, mo, 0))  # Mon

    # Dedup while preserving order, and keep only future-ish
    seen = set()
    res: List[str] = []
    for x in out:
        if x < today:
            continue
        s = x.strftime("%Y-%m-%d")
        if s in seen:
            continue
        seen.add(s)
        res.append(s)

    return res
