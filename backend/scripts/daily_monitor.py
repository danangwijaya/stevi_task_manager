"""Read-only health report of the polygon data, sent to Telegram (run by cron on the VPS host, not in a container).

    python3 daily_monitor.py [--dry] [--hours=8]     report now (cron: three times a day)
    python3 daily_monitor.py --poll                  answer Telegram commands (cron: every minute, with flock)

Commands, accepted only from TELEGRAM_CHAT_ID:  /periksa [hours]  report now (default 8, at most 168),
/fix [grid]  choose a grid and a repair script and see its DRY RUN (the bot never applies anything), /bantuan  help.
Needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in ~/.geostevia_monitor.env (KEY=VALUE per line, mode 600), docker access to
the geoai_postgis and geoai_backend containers and nothing but the standard library. It never writes to the database.
Only grid codes and counts go into the message, no mapper names. --dry prints the message instead of sending it.
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

ENV_FILE = os.path.expanduser("~/.geostevia_monitor.env")
WIB = timezone(timedelta(hours=7))
OFFSET_FILE = os.path.expanduser("~/geostevia_monitor/offset")
HELP = ("Perintah:\n/periksa [jam] : laporan sekarang (default 8 jam, maksimal 168)\n"
        "/fix [grid] : pilih grid lalu pilih pemeriksaan perbaikan (hanya dry-run, tidak mengubah data)\n/bantuan : pesan ini")
FIX_DIR = os.path.expanduser("~/geostevia_monitor/fix")
# kind -> (script, extra arguments, label). Nothing here ever passes --apply: the bot only shows what a script WOULD do.
FIX_SCRIPTS = {
    "d": ("dedupe_giants.py", ["--min-ha=10", "--min-iou=0.9"], "Salinan raksasa usang"),
    "o": ("resolve_overlaps.py", [], "Tumpang tindih"),
    "g": ("absorb_gaps.py", [], "Celah"),
}
FIX_KEEP = {"d": ("grid ", "cluster of", "polygons in grid"),
            "o": ("grid ", "overlapping", "cuttable", "[AFTER", "area removed"),
            "g": ("grid ", "[BEFORE", "plan:", "[AFTER")}


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


def psql_json(sql):
    out = subprocess.run(
        ["docker", "exec", "geoai_postgis", "psql", "-U", "geoai_user", "-d", "geoai_landcover", "-At", "-c",
         f"select coalesce(json_agg(t), '[]') from ({sql}) t"],
        capture_output=True, text=True, timeout=120, check=True).stdout
    return json.loads(out)


def format_ops(ops, limit=4):
    """'undo (3s) > split_poly x2 (1s)': the last operations of a client trail, with how long before the save they happened."""
    parts = []
    for o in (ops or [])[-limit:]:
        n = o.get("n")
        parts.append(f"{o.get('op', '?')}{f' x{n}' if n and n > 1 else ''} ({o.get('ago', '?')}s)")
    return " > ".join(parts)


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

    ctx_n, no_id_n, save_n = (int(x) for x in psql(
        f"select count(*) filter (where details::text like '%\"ctx\"%'), "
        f"count(*) filter (where (details::json->'ctx'->>'no_id')::int > 0), count(*) "
        f"from audit_logs where action = 'SAVE_ANNOTATIONS' and created_at > {since}")[0])
    events = psql_json(
        f"select to_char(a.created_at + interval '7 hours', 'HH24:MI') wib, coalesce(t.grid_code, a.task_grid_id::text) grid, "
        f"a.action, a.details::json->'ctx' ctx from audit_logs a left join task_grids t on t.id = a.task_grid_id "
        f"where (a.action = 'DUPLICATE_SUSPECT' or (a.action = 'SAVE_ANNOTATIONS' and a.details::text like '%dropped_duplicates%')) "
        f"and a.details::text like '%\"ctx\"%' and a.created_at > {since} order by a.id desc limit 5")
    trail = [f"{e['grid']} {e['wib']} WIB {'ditolak' if e['action'] == 'SAVE_ANNOTATIONS' else 'kembar'}: "
             f"{format_ops((e['ctx'] or {}).get('ops')) or '-'}; poligon tanpa id {(e['ctx'] or {}).get('no_id', '?')}"
             f"/{(e['ctx'] or {}).get('features', '?')}" for e in events]

    errors = backend_errors(hours)
    if errors:
        problems.append(f"Backend mencatat {errors} error (Traceback/500) dalam {hours} jam")

    now = datetime.now(WIB).strftime("%d %b %H:%M WIB")
    head = f"GEOSTEVIA {now} | {hours} jam terakhir\nSimpan: {saves_txt}"
    if ctx_n:
        head += f"\nJejak klien: {ctx_n} dari {save_n} simpan membawa ctx, {no_id_n} punya poligon tanpa id"
    elif save_n:
        head += "\nJejak klien: belum ada (klien belum hard refresh)"
    tail = ("\nJejak sebelum kembar:\n- " + "\n- ".join(trail)) if trail else ""
    if not problems:
        return head + "\nStatus: OK, tidak ada kembaran baru, raksasa bertumpuk, atau error." + tail
    return head + "\nStatus: PERLU DICEK\n- " + "\n- ".join(problems) + tail


def send(env, text, reply_markup=None):
    fields = {"chat_id": env["TELEGRAM_CHAT_ID"], "text": text[:3900]}
    if reply_markup:
        fields["reply_markup"] = reply_markup
    data = urllib.parse.urlencode(fields).encode()
    url = f"https://api.telegram.org/bot{env['TELEGRAM_BOT_TOKEN']}/sendMessage"
    with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as r:
        return r.status


def pick_events(updates, chat_id):
    """(events, next_offset): ('command', text) and ('callback', {id, data}) from the authorised chat, and the offset that
    acknowledges every update. Messages and button presses from any other chat are skipped without an answer."""
    events, next_offset = [], None
    for u in updates:
        next_offset = u["update_id"] + 1
        cb = u.get("callback_query")
        if cb:
            if str(((cb.get("message") or {}).get("chat") or {}).get("id")) == str(chat_id) and cb.get("data"):
                events.append(("callback", {"id": cb["id"], "data": cb["data"]}))
            continue
        msg = u.get("message") or {}
        if str((msg.get("chat") or {}).get("id")) != str(chat_id):
            continue
        text = (msg.get("text") or "").strip()
        if text.startswith("/"):
            events.append(("command", text))
    return events, next_offset


def parse_command(text, default_hours=8):
    """('report', hours) for /periksa [hours], ('fix', argument) for /fix [grid], ('help', None) for anything else."""
    word, *rest = text.split()
    word = word.split("@")[0].lower()
    if word == "/periksa":
        try:
            hours = int(rest[0]) if rest else default_hours
        except ValueError:
            hours = default_hours
        return "report", max(1, min(hours, 168))
    if word == "/fix":
        return "fix", " ".join(rest)
    return "help", None


def grid_pattern(arg):
    """ILIKE pattern for a grid typed by the mapper ('013' -> SB_GRID_013_%, '013_2022' -> %013_2022%); None if unsafe."""
    arg = arg.strip()
    if not re.fullmatch(r"[A-Za-z0-9_]{1,30}", arg):
        return None
    return f"SB_GRID_{int(arg):03d}_%" if arg.isdigit() else f"%{arg.upper()}%"


def fix_commands(kind, grid_id):
    """The docker commands that copy one repair script into the backend container and run it as a DRY RUN."""
    script, extra, _ = FIX_SCRIPTS[kind]
    return [["docker", "cp", f"{FIX_DIR}/{script}", f"geoai_backend:/tmp/{script}"],
            ["docker", "exec", "-e", "PYTHONPATH=/app", "geoai_backend", "python", "-W", "ignore", f"/tmp/{script}", str(int(grid_id)), *extra]]


def summarize_fix(kind, text):
    lines = [re.sub(r"created [0-9: .-]*", "", l.strip()) for l in text.splitlines() if l.strip().startswith(FIX_KEEP[kind])]
    if kind == "d":
        clusters = [l for l in lines if l.startswith("cluster of")]
        rest = [l for l in lines if not l.startswith("cluster of")]
        more = [f"... dan {len(clusters) - 5} kluster lain"] if len(clusters) > 5 else []
        lines = rest[:1] + clusters[:5] + more + rest[1:]
    return "\n".join(lines) or f"(tidak ada keluaran) {text[-200:]}"


def run_fix(kind, grid_id):
    text = ""
    for cmd in fix_commands(kind, grid_id):
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=480)
        text = done.stdout + done.stderr
    if "mode DRY RUN" not in text:                 # belt and braces: never show or trust anything that was not a dry run
        return "Dibatalkan: keluaran skrip bukan dry-run.\n" + text[-300:]
    return summarize_fix(kind, text)


def keyboard(rows):
    return json.dumps({"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in row] for row in rows]})


def find_grids(arg):
    pat = grid_pattern(arg)
    if not pat:
        return []
    return psql_json(f"select t.id, t.grid_code, t.status from task_grids t where t.grid_code ilike '{pat}' "
                     f"and exists (select 1 from annotations a where a.task_grid_id = t.id) order by t.grid_code limit 8")


def short(code):
    return code.replace("SB_GRID_", "")


def send_grid_choices(env, grids, title):
    send(env, title, keyboard([[(f"{short(g['grid_code'])} ({g['status']})", f"fx:g:{g['id']}")] for g in grids]))


def on_fix_text(env, arg):
    if not arg:
        recent = psql_json("select t.id, t.grid_code, t.status from audit_logs a join task_grids t on t.id = a.task_grid_id "
                           "where (a.action = 'DUPLICATE_SUSPECT' or a.details::text like '%dropped_duplicates%') "
                           "and a.created_at > now() - interval '72 hours' group by 1, 2, 3 order by count(*) desc limit 6")
        if recent:
            send_grid_choices(env, recent, "Grid dengan peringatan kembar 72 jam terakhir. Pilih, atau ketik /fix 013_2022:")
        else:
            send(env, "Ketik /fix diikuti kode grid, misalnya /fix 013_2022 atau /fix 013.")
        return
    grids = find_grids(arg)
    if not grids:
        send(env, f"Grid '{arg}' tidak ditemukan (atau belum punya poligon).")
    elif len(grids) == 1:
        send_actions(env, grids[0])
    else:
        send_grid_choices(env, grids, f"Beberapa grid cocok dengan '{arg}'. Pilih satu:")


def send_actions(env, g):
    rows = [[(label, f"fx:a:{g['id']}:{kind}")] for kind, (_, _, label) in FIX_SCRIPTS.items()]
    rows.append([("Ketiganya", f"fx:a:{g['id']}:all")])
    warn = "\nSTATUS INI TIDAK BOLEH DISENTUH, ini hanya dry-run." if g["status"] in ("SUBMITTED", "APPROVED") else ""
    send(env, f"{short(g['grid_code'])} ({g['status']}). Pilih pemeriksaan (dry-run, tidak mengubah data):{warn}", keyboard(rows))


def on_callback(env, cb):
    telegram_get(env, "answerCallbackQuery", callback_query_id=cb["id"])
    parts = cb["data"].split(":")
    if parts[0] != "fx" or len(parts) < 3 or not parts[2].isdigit():
        return
    rows = psql_json(f"select id, grid_code, status from task_grids where id = {int(parts[2])}")
    if not rows:
        send(env, "Grid tidak ditemukan.")
        return
    g = rows[0]
    if parts[1] == "g":
        send_actions(env, g)
        return
    if parts[1] != "a" or len(parts) < 4 or parts[3] not in (*FIX_SCRIPTS, "all"):
        return
    kinds = list(FIX_SCRIPTS) if parts[3] == "all" else [parts[3]]
    send(env, f"Menjalankan dry-run {short(g['grid_code'])}, bisa beberapa menit untuk grid besar...")
    for kind in kinds:
        try:
            out = run_fix(kind, g["id"])
        except Exception as exc:
            out = f"GAGAL: {type(exc).__name__}: {str(exc)[:200]}"
        send(env, f"{FIX_SCRIPTS[kind][2]} - {short(g['grid_code'])}\n{out}\n(dry-run: tidak ada data yang diubah)")


def telegram_get(env, method, **params):
    url = f"https://api.telegram.org/bot{env['TELEGRAM_BOT_TOKEN']}/{method}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def poll(env):
    """Answers the commands and button presses that arrived since the last poll. The offset is saved before answering, so
    one is never answered twice; the first run only acknowledges what is already waiting."""
    first = not os.path.exists(OFFSET_FILE)
    offset = 0 if first else int(open(OFFSET_FILE).read().strip() or 0)
    updates = telegram_get(env, "getUpdates", offset=offset, timeout=0,
                           allowed_updates=json.dumps(["message", "callback_query"])).get("result", [])
    events, next_offset = pick_events(updates, env["TELEGRAM_CHAT_ID"])
    if next_offset is None:
        return
    os.makedirs(os.path.dirname(OFFSET_FILE), exist_ok=True)
    with open(OFFSET_FILE, "w") as f:
        f.write(str(next_offset))
    if first:
        return
    for kind, payload in events[:3]:
        try:
            if kind == "callback":
                on_callback(env, payload)
                print("button", payload["data"])
                continue
            action, arg = parse_command(payload)
            if action == "help":
                send(env, HELP)
            elif action == "fix":
                on_fix_text(env, arg)
            else:
                send(env, f"Memeriksa {arg} jam terakhir, tunggu sebentar...")
                try:
                    report = build_report(arg)
                except Exception as exc:
                    report = f"GEOSTEVIA monitor GAGAL jalan: {type(exc).__name__}: {str(exc)[:200]}"
                send(env, report)
            print("answered", payload)
        except Exception as exc:
            print("poll error", type(exc).__name__, str(exc)[:200], file=sys.stderr)
            send(env, f"GEOSTEVIA bot gagal menjawab: {type(exc).__name__}: {str(exc)[:200]}")


if __name__ == "__main__":
    if "--poll" in sys.argv:
        poll(load_env())
        sys.exit(0)
    hours = next((int(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("--hours=")), 8)
    try:
        report = build_report(hours)
    except Exception as exc:                      # silence must not look like success
        report = f"GEOSTEVIA monitor GAGAL jalan: {type(exc).__name__}: {str(exc)[:200]}"
    if "--dry" in sys.argv:
        print(report)
    else:
        print("telegram status", send(load_env(), report))
