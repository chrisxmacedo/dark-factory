#!/usr/bin/env python3
"""Working-day arithmetic for the office calendar.

Weekends are Saturday and Sunday. Optional holidays live in
config/holidays.txt, one ISO date per line. The file is a local calendar,
not a country pack baked into the template.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path


def office_root() -> Path:
    here = Path(__file__).resolve().parent
    for ancestor in [here.parent, *here.parents]:
        if (ancestor / "config").is_dir() and (ancestor / "scripts").is_dir():
            return ancestor
    return here.parent


def parse_date(value: str) -> date:
    text = value.strip()
    if "T" in text:
        text = text.split("T", 1)[0]
    return date.fromisoformat(text)


def load_holidays(path: Path | None) -> set[date]:
    if path is None or not path.is_file():
        return set()
    holidays: set[date] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            holidays.add(parse_date(line))
    return holidays


def is_working_day(day: date, holidays: set[date]) -> bool:
    return day.weekday() < 5 and day not in holidays


def working_day_number(day: date, holidays: set[date]) -> int | None:
    """1-based index of this date among working days in its month."""
    if not is_working_day(day, holidays):
        return None
    cursor = date(day.year, day.month, 1)
    count = 0
    while cursor <= day:
        if is_working_day(cursor, holidays):
            count += 1
        cursor += timedelta(days=1)
    return count


def nth_working_day(year: int, month: int, n: int, holidays: set[date]) -> date:
    if n < 1:
        raise ValueError("working day number starts at 1")
    cursor = date(year, month, 1)
    seen = 0
    while cursor.month == month:
        if is_working_day(cursor, holidays):
            seen += 1
            if seen == n:
                return cursor
        cursor += timedelta(days=1)
    raise ValueError(f"{year}-{month:02d} has no working day {n}")


def subtract_working_days(day: date, n: int, holidays: set[date]) -> date:
    """The working day that is n working days before `day`. `day` itself is not counted."""
    if n < 1:
        raise ValueError("n starts at 1")
    cursor = day
    seen = 0
    while seen < n:
        cursor -= timedelta(days=1)
        if is_working_day(cursor, holidays):
            seen += 1
    return cursor


def next_quarter_start(day: date) -> date:
    starts = [date(day.year, month, 1) for month in (1, 4, 7, 10)]
    starts.append(date(day.year + 1, 1, 1))
    for start in starts:
        if start > day:
            return start
    return date(day.year + 1, 1, 1)


def previous_working_day(day: date, holidays: set[date]) -> date:
    cursor = day
    while not is_working_day(cursor, holidays):
        cursor -= timedelta(days=1)
    return cursor


def quarterly_due(day: date, lead_days: int, holidays: set[date]) -> bool:
    """True when `day` is the run date for the next quarter.

    The deadline is `lead_days` calendar days before the quarter starts.
    If that date is not a working day, the run moves to the working day before it.
    """
    nominal = next_quarter_start(day) - timedelta(days=lead_days)
    due = nominal if is_working_day(nominal, holidays) else previous_working_day(nominal, holidays)
    return day == due


def board_due(day: date, board_dates: list[date], working_days_before: int, holidays: set[date]) -> date | None:
    for board in board_dates:
        if subtract_working_days(board, working_days_before, holidays) == day:
            return board
    return None


def default_holidays(root: Path | None = None) -> set[date]:
    root = root or office_root()
    return load_holidays(root / "config" / "holidays.txt")


def main() -> None:
    parser = argparse.ArgumentParser(description="Office working-day calculations")
    parser.add_argument("--date", help="ISO date to describe")
    parser.add_argument("--before", help="Count working days before this ISO date")
    parser.add_argument("--days", type=int, default=10)
    parser.add_argument("--holidays", type=Path, help="Holiday file (default: config/holidays.txt if present)")
    args = parser.parse_args()
    holidays = load_holidays(args.holidays) if args.holidays else default_holidays()
    if args.before:
        found = subtract_working_days(parse_date(args.before), args.days, holidays)
        print(found.isoformat())
        return
    day = parse_date(args.date) if args.date else date.today()
    number = working_day_number(day, holidays)
    print(f"date={day.isoformat()}")
    print(f"working_day={number if number is not None else 'no'}")
    print(f"quarterly_due={str(quarterly_due(day, 7, holidays)).lower()}")


if __name__ == "__main__":
    main()
