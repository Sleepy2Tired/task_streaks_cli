from __future__ import annotations
import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

ROOT = Path(__file__).parent
DB_FILE = ROOT / "streaks.json"
DATE_FMT = "%Y-%m-%d"

# ------------- Models & Storage -------------

@dataclass
class Task:
    name: str
    created_at: str  # ISO
    done_days: List[str]  # list of YYYY-MM-DD

def today_str() -> str:
    return datetime.now().strftime(DATE_FMT)

def load_db() -> Dict[str, Any]:
    if not DB_FILE.exists():
        return {"tasks": {}}
    try:
        return json.loads(DB_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"tasks": {}}

def save_db(db: Dict[str, Any]) -> None:
    DB_FILE.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")

def get_task(db: Dict[str, Any], name: str) -> Optional[Task]:
    raw = db["tasks"].get(name.lower())
    if not raw:
        return None
    return Task(name=raw["name"], created_at=raw["created_at"], done_days=list(raw.get("done_days", [])))

def put_task(db: Dict[str, Any], task: Task) -> None:
    db["tasks"][task.name.lower()] = {
        "name": task.name,
        "created_at": task.created_at,
        "done_days": sorted(list(set(task.done_days)))
    }

# ------------- Streak Math -------------

def str_to_date(s: str) -> datetime:
    return datetime.strptime(s, DATE_FMT)

def date_to_str(d: datetime) -> str:
    return d.strftime(DATE_FMT)

def compute_streaks(done_days: List[str]) -> Dict[str, int]:
    """Return current_streak and best_streak given a list of YYYY-MM-DD strings."""
    if not done_days:
        return {"current": 0, "best": 0}
    days = sorted(set(done_days))
    # best streak
    best = 1
    cur = 1
    for i in range(1, len(days)):
        d_prev = str_to_date(days[i - 1])
        d_cur  = str_to_date(days[i])
        if d_cur - d_prev == timedelta(days=1):
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    # current streak (ending today/yesterday)
    today = str_to_date(today_str())
    dayset = set(days)
    # Walk backwards from today while days exist
    cur_today = 0
    probe = today
    while date_to_str(probe) in dayset:
        cur_today += 1
        probe -= timedelta(days=1)
    # If not today, try starting yesterday (allows checking after midnight)
    if cur_today == 0:
        probe = today - timedelta(days=1)
        while date_to_str(probe) in dayset:
            cur_today += 1
            probe -= timedelta(days=1)
    return {"current": cur_today, "best": best}

def mini_calendar(done_days: List[str], span: int = 14) -> str:
    """Return a compact 14-day calendar line: O = done, . = missed, with dates underneath."""
    today = datetime.now().date()
    dayset = set(done_days)
    marks = []
    dates = []
    for i in range(span - 1, -1, -1):
        d = today - timedelta(days=i)
        s = d.strftime(DATE_FMT)
        marks.append("O" if s in dayset else ".")
        dates.append(d.strftime("%m-%d"))
    return "".join(marks) + "\n" + " ".join(dates)

# ------------- Commands -------------

def cmd_add(args) -> int:
    db = load_db()
    name = " ".join(args.name).strip()
    if not name:
        print('Provide a task name, e.g. add "Write code"')
        return 1
    if name.lower() in db["tasks"]:
        print("Task already exists.")
        return 1
    t = Task(name=name, created_at=datetime.now().isoformat(timespec="seconds"), done_days=[])
    put_task(db, t)
    save_db(db)
    print(f"✅ Added task: {name}")
    return 0

def cmd_list(_args) -> int:
    db = load_db()
    if not db["tasks"]:
        print("No tasks yet. Add one with: add \"Write code\"")
        return 0
    print("Tasks:")
    for k, raw in sorted(db["tasks"].items()):
        t = get_task(db, raw["name"])
        streaks = compute_streaks(t.done_days)
        print(f" - {t.name}  (current: {streaks['current']}, best: {streaks['best']}, total days: {len(t.done_days)})")
    return 0

def cmd_done(args) -> int:
    db = load_db()
    name = " ".join(args.name).strip()
    if not name:
        print('Usage: done "Write code"')
        return 1
    t = get_task(db, name)
    if not t:
        print("No such task. Add it first with: add \"...\"")
        return 1
    day = today_str()
    if day in t.done_days:
        print(f"Already marked done today for: {t.name}")
        return 0
    t.done_days.append(day)
    put_task(db, t)
    save_db(db)
    print(f"✅ Marked done for {t.name} on {day}")
    return 0

def cmd_undo(args) -> int:
    db = load_db()
    name = " ".join(args.name).strip()
    if not name:
        print('Usage: undo "Write code"')
        return 1
    t = get_task(db, name)
    if not t:
        print("No such task.")
        return 1
    day = today_str()
    if day in t.done_days:
        t.done_days = [d for d in t.done_days if d != day]
        put_task(db, t)
        save_db(db)
        print(f"↩️ Removed today’s completion for {t.name}")
    else:
        print("Nothing to undo for today.")
    return 0

def cmd_streaks(args) -> int:
    db = load_db()
    name = " ".join(args.name).strip() if args.name else ""
    if name:
        t = get_task(db, name)
        if not t:
            print("No such task.")
            return 1
        s = compute_streaks(t.done_days)
        print(f"{t.name} → current: {s['current']}, best: {s['best']}, total days: {len(t.done_days)}")
        print(mini_calendar(t.done_days))
        return 0
    # overall summary
    best_any = 0
    for raw in db["tasks"].values():
        s = compute_streaks(raw.get("done_days", []))
        best_any = max(best_any, s["best"])
    print(f"Overall best streak across tasks: {best_any}")
    return 0

def cmd_calendar(args) -> int:
    db = load_db()
    name = " ".join(args.name).strip()
    t = get_task(db, name)
    if not t:
        print("No such task.")
        return 1
    print(t.name)
    print(mini_calendar(t.done_days, span=args.days))
    return 0

def cmd_stats(_args) -> int:
    db = load_db()
    total_marks = sum(len(raw.get("done_days", [])) for raw in db["tasks"].values())
    print(f"Total checkmarks: {total_marks}")
    for raw in db["tasks"].values():
        t = get_task(db, raw["name"])
        s = compute_streaks(t.done_days)
        print(f" - {t.name}: {len(t.done_days)} marks (current {s['current']}, best {s['best']})")
    return 0

# ------------- Arg Parser -------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="streaks",
        description="Track daily tasks and streaks."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help='Add a task, e.g. add "Write code"')
    add.add_argument("name", nargs="+")
    add.set_defaults(func=cmd_add)

    ls = sub.add_parser("list", help="List tasks with current/best streaks")
    ls.set_defaults(func=cmd_list)

    dn = sub.add_parser("done", help='Mark task done for today, e.g. done "Write code"')
    dn.add_argument("name", nargs="+")
    dn.set_defaults(func=cmd_done)

    ud = sub.add_parser("undo", help='Undo today for a task, e.g. undo "Write code"')
    ud.add_argument("name", nargs="+")
    ud.set_defaults(func=cmd_undo)

    st = sub.add_parser("streaks", help='Show streaks for a task or overall, e.g. streaks "Write code"')
    st.add_argument("name", nargs="*")
    st.set_defaults(func=cmd_streaks)

    cal = sub.add_parser("calendar", help='Mini-calendar for a task (last N days)')
    cal.add_argument("name", nargs="+")
    cal.add_argument("--days", type=int, default=14)
    cal.set_defaults(func=cmd_calendar)

    stats = sub.add_parser("stats", help="Totals per task")
    stats.set_defaults(func=cmd_stats)

    return p

def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())
