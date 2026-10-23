"""Read-only health report of the polygon data, sent to Telegram (run by cron on the VPS host, not in a container).

    python3 daily_monitor.py [--dry] [--hours=8]

Needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in ~/.geostevia_monitor.env (KEY=VALUE per line, mode 600), docker access to
the geoai_postgis and geoai_backend containers and nothing but the standard library. It never writes to the database.
Only grid codes and counts go into the message, no mapper names. --dry prints the message instead of sending it.
"""
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

ENV_FILE = os.path.expanduser("~/.geostevia_monitor.env")
WIB = timezone(timedelta(hours=7))


def load_env():
    env = {}
    with open(ENV_FILE) as f:
        for line in f:
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.strip().split("=", 1)
                env[k] = v
    return env


def psql(sql):
    out = subprocess.run(
        ["docker", "exec", "geoai_postgis", "psql", "-U", "geoai_user", "-d", "geoai_landcover", "-At", "-F", "|", "-c", sql],
        capture_output=True, text=True, timeout=120, check=True).stdout
    return [line.split("|") for line in out.splitlines() if line and line != "SET"]


def backend_errors(hours):
    out = subprocess.run(["docker", "logs", "--since", f"{hours}h", "geoai_backend"],
                         capture_output=True, text=True, timeout=120)
    text = out.stdout + out.stderr
    return sum(1 for line in text.splitlines() if "Traceback" in line or "Internal Server Error" in line)


def build_report(hours):
    since = f"now() - interval '{hours} hours'"
    problems = []

    saves = psql(f"select coalesce(details::json->>'mode','full'), count(*) from audit_logs "
                 f"where action='SAVE_ANNOTATIONS' and created_at > {since} group by 1 order by 1")
    saves_txt = ", ".join(f"{m} {n}" for m, n in saves) or "tidak ada"

    dup = psql(f"select coalesce(t.grid_code, a.task_grid_id::text), count(*) from audit_logs a "
               f"left join task_grids t on t.id = a.task_grid_id "
               f"where a.action='DUPLICATE_SUSPECT' and a.created_at > {since} group by 1 order by 2 desc limit 8")
    if dup:
        problems.append("Peringatan kembar (DUPLICATE_SUSPECT): " + ", ".join(f"{g} x{n}" for g, n in dup))

    dropped = psql(f"select coalesce(t.grid_code, a.task_grid_id::text), count(*) from audit_logs a "
                   f"left join task_grids t on t.id = a.task_grid_id "
                   f"where a.action='SAVE_ANNOTATIONS' and a.details::text like '%dropped_duplicates%' "
                   f"and a.created_at > {since} group by 1 order by 2 desc limit 8")
    if dropped:
        problems.append("Sisipan kembar ditolak server: " + ", ".join(f"{g} x{n}" for g, n in dropped))

    twins = psql("set statement_timeout = '60s'; set max_parallel_workers_per_gather = 0; "
                 "with c as (select t.grid_code, x.geom_geojson ga, y.geom_geojson gb from annotations x "
                 "join annotations y on y.task_grid_id = x.task_grid_id and y.id > x.id and y.class_id = x.class_id "
                 "and y.area_sqm between x.area_sqm * 0.95 and x.area_sqm * 1.05 "
                 "join task_grids t on t.id = x.task_grid_id where x.area_sqm > 1e7), "
                 "g as (select grid_code, st_makevalid(st_geomfromgeojson(ga)) a, st_makevalid(st_geomfromgeojson(gb)) b from c) "
                 "select grid_code, count(*) from g where st_intersects(a, b) "
                 "and st_area(st_intersection(a, b)) / least(st_area(a), st_area(b)) > 0.9 group by 1 order by 2 desc limit 8")
    if twins:
        problems.append("Poligon >= 1.000 ha yang saling menutup >90% dengan kelas sama (kembar): "
                        + ", ".join(f"{g} x{n}" for g, n in twins))

    errors = backend_errors(hours)
    if errors:
        problems.append(f"Backend mencatat {errors} error (Traceback/500) dalam {hours} jam")

    now = datetime.now(WIB).strftime("%d %b %H:%M WIB")
    head = f"GEOSTEVIA {now} | {hours} jam terakhir\nSimpan: {saves_txt}"
    if not problems:
        return head + "\nStatus: OK, tidak ada kembaran baru, raksasa bertumpuk, atau error."
    return head + "\nStatus: PERLU DICEK\n- " + "\n- ".join(problems)


def send(env, text):
    data = urllib.parse.urlencode({"chat_id": env["TELEGRAM_CHAT_ID"], "text": text}).encode()
    url = f"https://api.telegram.org/bot{env['TELEGRAM_BOT_TOKEN']}/sendMessage"
    with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as r:
        return r.status


if __name__ == "__main__":
    hours = next((int(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("--hours=")), 8)
    try:
        report = build_report(hours)
    except Exception as exc:                      # silence must not look like success
        report = f"GEOSTEVIA monitor GAGAL jalan: {type(exc).__name__}: {str(exc)[:200]}"
    if "--dry" in sys.argv:
        print(report)
    else:
        print("telegram status", send(load_env(), report))
