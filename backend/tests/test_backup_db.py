import importlib.util
from datetime import datetime, timedelta
from pathlib import Path

spec = importlib.util.spec_from_file_location("backup_db", Path(__file__).resolve().parents[1] / "scripts" / "backup_db.py")
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


def names(start, days, per_day=1):
    out = []
    for d in range(days):
        for h in range(per_day):
            out.append((start + timedelta(days=d, hours=h)).strftime("geoai_%Y%m%d_%H%M.dump"))
    return out


def test_retention_keeps_the_newest_seven_and_one_per_week_for_four_weeks():
    files = names(datetime(2026, 9, 1, 18, 30), 56)                       # 8 weeks of daily backups
    gone = backup.select_deletions(files)
    kept = sorted(set(files) - set(gone))
    assert len(kept) == 7 + 4
    assert files[-1] in kept and files[-7] in kept                         # the newest seven
    assert files[0] in gone                                                # the oldest are gone
    older = [backup.stamp_of(n).isocalendar()[:2] for n in kept[:-7]]
    assert len(older) == len(set(older)) == 4                              # one per ISO week


def test_retention_never_touches_files_that_are_not_ours_and_keeps_everything_when_there_are_few():
    files = names(datetime(2026, 10, 1, 18, 30), 5) + ["backup_g013_20261023_1603.dump", "latest.json", "geoai_notadate.dump"]
    assert backup.select_deletions(files) == []


def test_restored_counts_must_exist_and_not_fall_below_the_counts_at_backup_time():
    expected = {"users": 30, "annotations": 100000, "audit_logs": 5000}
    assert backup.counts_ok({"users": 30, "annotations": 100010, "audit_logs": 5000}, expected) == []
    assert backup.counts_ok({"users": 30, "annotations": 99500, "audit_logs": 5000}, expected) == []        # within 1 percent
    bad = backup.counts_ok({"users": 30, "annotations": 50000}, expected)
    assert any("annotations" in p for p in bad) and any("audit_logs" in p and "tidak ada" in p for p in bad)
