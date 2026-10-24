"""Automatic database backup, retention and restore drill (cron on the VPS host, not in a container).

    python3 backup_db.py            take a backup, verify it, rotate old ones, copy it off the server (if configured), report
    python3 backup_db.py --drill    restore the newest backup into a throwaway database and compare row counts
    python3 backup_db.py --dry      show what a backup run would do

Backups go to ~/backups_auto (geoai_YYYYmmdd_HHMM.dump + .json, newest 7 files and the newest of each of the last 4 weeks are kept;
the manual backup_*.dump files in ~ are never touched). A backup counts only when `pg_restore -l` can read it and its sha256 is
recorded. Offsite copy: set OFFSITE_RSYNC (user@host:/dir/) or OFFSITE_RCLONE (remote:dir, plus OFFSITE_KEEP_DAYS, default 8) in ~/.geostevia_backup.env. The Telegram
report uses the token and chat id of ~/.geostevia_monitor.env. Standard library only; it never changes the live database.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

HOME = os.path.expanduser("~")
BACKUP_DIR = os.path.join(HOME, "backups_auto")
BACKUP_ENV = os.path.join(HOME, ".geostevia_backup.env")
MONITOR_ENV = os.path.join(HOME, ".geostevia_monitor.env")
PG_CONTAINER, PG_USER, DB = "geoai_postgis", "geoai_user", "geoai_landcover"
DRILL_DB = "geoai_restore_drill"
COUNT_TABLES = ("users", "task_grids", "annotations", "audit_logs")
KEEP_DAILY, KEEP_WEEKLY = 7, 4
MIN_FREE_GB = 20
MIN_TOC_LINES = 100
NAME_RE = re.compile(r"^geoai_(\d{8})_(\d{4})\.dump$")
WIB = timezone(timedelta(hours=7))


def read_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path):
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.strip().split("=", 1)
                env[k] = v
    return env


def stamp_of(name):
    m = NAME_RE.match(name)
    return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M") if m else None


def select_deletions(names, keep_daily=KEEP_DAILY, keep_weekly=KEEP_WEEKLY):
    """Which backup file names to delete: keep the newest `keep_daily`, plus the newest one of each of the `keep_weekly` most
    recent ISO weeks among the older ones. Names that do not look like our backups are never returned."""
    stamped = sorted(((stamp_of(n), n) for n in names if stamp_of(n)), reverse=True)
    keep = {n for _, n in stamped[:keep_daily]}
    seen_weeks = []
    for ts, n in stamped[keep_daily:]:
        week = ts.isocalendar()[:2]
        if week not in seen_weeks and len(seen_weeks) < keep_weekly:
            seen_weeks.append(week)
            keep.add(n)
    return sorted(n for _, n in stamped if n not in keep)


def counts_ok(restored, expected, tolerance=0.01):
    """Restored row counts must be present and not below the counts taken at backup time (minus tolerance)."""
    problems = []
    for table, want in expected.items():
        got = restored.get(table)
        if got is None:
            problems.append(f"{table}: tabel tidak ada")
        elif want > 0 and got < want * (1 - tolerance):
            problems.append(f"{table}: {got} < {want}")
    return problems


def docker_psql(sql, db):
    out = subprocess.run(["docker", "exec", PG_CONTAINER, "psql", "-U", PG_USER, "-d", db, "-At", "-c", sql],
                         capture_output=True, text=True, timeout=300, check=True).stdout
    return out.strip()


def table_counts(db):
    result = {}
    for table in COUNT_TABLES:
        try:
            result[table] = int(docker_psql(f"select count(*) from {table}", db))
        except Exception:
            pass
    return result


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def toc_lines(path):
    with open(path, "rb") as f:
        out = subprocess.run(["docker", "exec", "-i", PG_CONTAINER, "pg_restore", "-l"], stdin=f, capture_output=True, timeout=600, check=True).stdout
    return len(out.splitlines())


def free_gb(path):
    return shutil.disk_usage(path).free / 1e9


def notify(text):
    env = read_env(MONITOR_ENV)
    if not env.get("TELEGRAM_BOT_TOKEN") or not env.get("TELEGRAM_CHAT_ID"):
        print("(no Telegram credentials)", text)
        return
    data = urllib.parse.urlencode({"chat_id": env["TELEGRAM_CHAT_ID"], "text": text[:3900]}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{env['TELEGRAM_BOT_TOKEN']}/sendMessage", data=data), timeout=30)
    except Exception as exc:                    # a failed message must not turn a good backup into a failed one
        print("telegram failed:", exc, file=sys.stderr)


def offsite(path):
    env = read_env(BACKUP_ENV)
    try:
        if env.get("OFFSITE_RSYNC"):
            subprocess.run(["rsync", "-a", "--partial", path, env["OFFSITE_RSYNC"]], check=True, timeout=3600, capture_output=True)
            return f"rsync ke {env['OFFSITE_RSYNC'].split(':')[0]}: berhasil"
        if env.get("OFFSITE_RCLONE"):
            remote, keep_days = env["OFFSITE_RCLONE"], int(env.get("OFFSITE_KEEP_DAYS", "8"))
            subprocess.run(["rclone", "copy", path, remote], check=True, timeout=7200, capture_output=True)
            # a cloud drive has a small quota: only the newest days stay there (the local disk keeps the 7 daily and 4 weekly files)
            subprocess.run(["rclone", "delete", remote, "--min-age", f"{keep_days}d", "--include", "geoai_*.dump"], check=True, timeout=1800, capture_output=True)
            return f"rclone ke {remote.split(':')[0]}: berhasil (salinan lebih dari {keep_days} hari di sana dihapus)"
    except Exception as exc:
        return f"GAGAL: {type(exc).__name__}"
    return "belum dikonfigurasi (cadangan hanya ada di server ini)"


def backup(dry=False):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if free_gb(BACKUP_DIR) < MIN_FREE_GB:
        raise RuntimeError(f"ruang disk kurang dari {MIN_FREE_GB} GB")
    name = datetime.now(timezone.utc).strftime("geoai_%Y%m%d_%H%M.dump")
    path = os.path.join(BACKUP_DIR, name)
    if dry:
        print("would write", path, "| would delete", select_deletions(os.listdir(BACKUP_DIR) + [name]))
        return
    counts = table_counts(DB)
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        subprocess.run(["docker", "exec", PG_CONTAINER, "pg_dump", "-U", PG_USER, "-Fc", DB], stdout=f, check=True, timeout=3600)
    lines = toc_lines(tmp)
    if lines < MIN_TOC_LINES:
        os.remove(tmp)
        raise RuntimeError(f"cadangan tidak terbaca utuh (hanya {lines} entri)")
    os.rename(tmp, path)
    meta = {"file": name, "size_mb": round(os.path.getsize(path) / 1e6, 1), "sha256": sha256_of(path), "toc_lines": lines,
            "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "counts": counts, "verified": True}
    meta["offsite"] = offsite(path)
    with open(path + ".json", "w") as f:
        json.dump(meta, f)
    with open(os.path.join(BACKUP_DIR, "latest.json"), "w") as f:
        json.dump(meta, f)
    gone = select_deletions(os.listdir(BACKUP_DIR))
    for n in gone:
        for suffix in ("", ".json"):
            try:
                os.remove(os.path.join(BACKUP_DIR, n + suffix))
            except FileNotFoundError:
                pass
    kept = len([n for n in os.listdir(BACKUP_DIR) if NAME_RE.match(n)])
    notify(f"GEOSTEVIA cadangan OK {datetime.now(WIB).strftime('%d %b %H:%M WIB')}\n{name} | {meta['size_mb']} MB | {lines} entri terbaca\n"
           f"Poligon saat itu: {counts.get('annotations', '?')} | disimpan {kept} berkas, dihapus {len(gone)}\nSalinan luar server: {meta['offsite']}")


def drill():
    files = sorted(n for n in os.listdir(BACKUP_DIR) if NAME_RE.match(n)) if os.path.isdir(BACKUP_DIR) else []
    if not files:
        raise RuntimeError("tidak ada cadangan otomatis untuk dilatih")
    name = files[-1]
    path = os.path.join(BACKUP_DIR, name)
    meta = json.load(open(path + ".json"))
    if free_gb(BACKUP_DIR) < MIN_FREE_GB:
        raise RuntimeError(f"ruang disk kurang dari {MIN_FREE_GB} GB")
    if sha256_of(path) != meta["sha256"]:
        raise RuntimeError("sha256 berkas cadangan berubah sejak dibuat")
    assert DRILL_DB != DB
    started = datetime.now(timezone.utc)
    problems = []
    restored = {}
    subprocess.run(["docker", "exec", PG_CONTAINER, "dropdb", "-U", PG_USER, "--if-exists", DRILL_DB], check=True, capture_output=True, timeout=300)
    subprocess.run(["docker", "exec", PG_CONTAINER, "createdb", "-U", PG_USER, DRILL_DB], check=True, capture_output=True, timeout=300)
    try:
        with open(path, "rb") as f:
            run = subprocess.run(["docker", "exec", "-i", PG_CONTAINER, "pg_restore", "-U", PG_USER, "--no-owner", "--no-privileges", "-d", DRILL_DB],
                                 stdin=f, capture_output=True, text=True, timeout=7200)
        if run.returncode not in (0, 1):                 # 1 = finished with warnings (extensions already present)
            problems.append(f"pg_restore keluar dengan kode {run.returncode}: {run.stderr[-200:]}")
        restored = table_counts(DRILL_DB)
        problems += counts_ok(restored, meta.get("counts", {}))
    finally:
        subprocess.run(["docker", "exec", PG_CONTAINER, "dropdb", "-U", PG_USER, "--if-exists", DRILL_DB], capture_output=True, timeout=300)
    minutes = round((datetime.now(timezone.utc) - started).total_seconds() / 60, 1)
    if problems:
        notify(f"GEOSTEVIA latihan pemulihan GAGAL ({name})\n- " + "\n- ".join(problems))
        sys.exit(1)
    notify(f"GEOSTEVIA latihan pemulihan OK ({name})\nDipulihkan ke database sementara dalam {minutes} menit; poligon {restored.get('annotations', '?')} "
           f"(saat cadangan {meta['counts'].get('annotations', '?')}). Database sementara sudah dihapus.")


if __name__ == "__main__":
    try:
        if "--drill" in sys.argv:
            drill()
        else:
            backup(dry="--dry" in sys.argv)
    except SystemExit:
        raise
    except Exception as exc:                      # silence must not look like success
        notify(f"GEOSTEVIA cadangan GAGAL: {type(exc).__name__}: {str(exc)[:300]}")
        sys.exit(1)
