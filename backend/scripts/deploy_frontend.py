"""Deploy the frontend (nginx + built app) of a given commit on the VPS host, unattended, with a config test and a rollback.

    python3 deploy_frontend.py --sha <commit> [--dry] [--cron-marker=<text>]

What it does, in this order, and stops at the first problem:
  1. wait until nobody has saved for a minute (at most 10 minutes), so an autosave is not cut in half by the restart
  2. fast-forward ~/app/stevi to exactly <commit> (a tracked change on the server aborts the deploy)
  3. keep the running image, build the new one and run `nginx -t` with it inside the compose network
  4. replace the container (the backend is not touched) and check the site: page, /version.json, /api/v1/health, security headers
  5. any failed check puts the old image and the old commit back and checks again
  6. report to Telegram and remove its own cron line (--cron-marker)
Standard library only. Telegram credentials: ~/.geostevia_monitor.env.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

REPO = os.path.expanduser("~/app/stevi")
COMPOSE = ["docker", "compose", "-f", "docker-compose.prod.yml"]
SERVICE, CONTAINER, NETWORK = "frontend", "geoai_frontend", "stevi_default"
ENV_FILE = os.path.expanduser("~/.geostevia_monitor.env")
LOG = os.path.expanduser("~/geostevia_monitor/deploy.log")


def log(msg):
    line = f"{time.strftime('%F %T')} {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def run(cmd, **kw):
    kw.setdefault("cwd", REPO)
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    kw.setdefault("timeout", 1800)
    return subprocess.run(cmd, check=True, **kw)


def notify(text):
    env = {}
    try:
        for line in open(ENV_FILE):
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.strip().split("=", 1)
                env[k] = v
        data = urllib.parse.urlencode({"chat_id": env["TELEGRAM_CHAT_ID"], "text": text[:3900]}).encode()
        urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{env['TELEGRAM_BOT_TOKEN']}/sendMessage", data=data), timeout=30)
    except Exception as exc:
        log(f"telegram failed: {exc}")


def strip_cron_line(crontab_text, marker):
    """The crontab without the line(s) that contain `marker`; a trailing newline is kept."""
    kept = [l for l in crontab_text.splitlines() if marker not in l]
    return "\n".join(kept) + "\n"


def remove_own_cron_line(marker):
    if not marker:
        return
    current = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    subprocess.run(["crontab", "-"], input=strip_cron_line(current, marker), text=True, check=True)


def recent_saves(seconds=60):
    out = subprocess.run(["docker", "exec", "geoai_postgis", "psql", "-U", "geoai_user", "-d", "geoai_landcover", "-At", "-c",
                          f"select count(*) from audit_logs where action = 'SAVE_ANNOTATIONS' and created_at > now() - interval '{seconds} seconds'"],
                         capture_output=True, text=True, timeout=60).stdout.strip()
    return int(out or 0)


def wait_until_quiet(max_minutes=10):
    deadline = time.time() + max_minutes * 60
    while time.time() < deadline:
        if recent_saves() == 0:
            return True
        log("someone is saving, waiting 30 s")
        time.sleep(30)
    return False


def curl(path, host="geostevia.id", head=False):
    cmd = ["curl", "-sk", "-m", "15", "-H", f"Host: {host}", "-w", "\n%{http_code}"] + (["-I"] if head else []) + [f"https://localhost{path}"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    body, _, code = out.rpartition("\n")
    return int(code or 0), body


def site_problems(new_build=True):
    """What is wrong with the site. `new_build=False` (after a rollback) only asks that the page and the API answer."""
    problems = []
    code, _ = curl("/")
    if code != 200:
        problems.append(f"halaman utama {code}")
    build = None
    if new_build:
        code, body = curl("/version.json")
        try:
            build = json.loads(body).get("build")
        except Exception:
            build = None
        if code != 200 or not build:
            problems.append(f"/version.json {code}")
    code, _ = curl("/api/v1/health")
    if code != 200:
        problems.append(f"/api/v1/health {code}")
    if new_build:
        _, headers = curl("/", head=True)
        if "strict-transport-security" not in headers.lower():
            problems.append("header HSTS tidak ada")
    return problems, build


def image_name():
    images = run(COMPOSE + ["config", "--images"]).stdout.split()
    return next(i for i in images if i.endswith("-frontend") or i.endswith("_frontend"))


def deploy(sha, dry):
    prev_head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    image = image_name()
    old_image_id = run(["docker", "inspect", CONTAINER, "--format", "{{.Image}}"]).stdout.strip()
    log(f"plan: {prev_head[:8]} -> {sha[:8]}, image {image}, running image {old_image_id[:19]}")
    if dry:
        log("dry run: nothing changed")
        return True
    if subprocess.run(["git", "diff", "--quiet"], cwd=REPO).returncode != 0:
        raise RuntimeError("ada perubahan yang belum di-commit di repo server; deploy dibatalkan")
    if not wait_until_quiet():
        log("saves never stopped for a minute: deploying anyway, autosave retries on its own")
    run(["git", "fetch", "origin"])
    run(["git", "merge", "--ff-only", sha])
    if run(["git", "rev-parse", "HEAD"]).stdout.strip() != sha:
        raise RuntimeError("HEAD bukan commit yang diminta")

    def roll_back(reason):
        log(f"ROLLBACK: {reason}")
        run(["docker", "tag", old_image_id, image])
        run(COMPOSE + ["up", "-d", "--no-deps", "--no-build", SERVICE])
        run(["git", "reset", "--hard", prev_head])
        time.sleep(8)
        again, _ = site_problems(new_build=False)
        notify(f"GEOSTEVIA deploy frontend DIBATALKAN dan dikembalikan ({reason}).\nSetelah pengembalian: {'normal' if not again else 'MASIH BERMASALAH: ' + ', '.join(again)}")
        return False

    try:
        run(COMPOSE + ["build", SERVICE])
        run(["docker", "run", "--rm", "--network", NETWORK, "-v", f"{REPO}/certbot/conf:/etc/letsencrypt:ro", image, "nginx", "-t"])
    except subprocess.CalledProcessError as exc:
        log(f"build or nginx -t failed: {exc.stderr[-400:] if exc.stderr else exc}")
        run(["git", "reset", "--hard", prev_head])
        notify("GEOSTEVIA deploy frontend dibatalkan sebelum mengganti apa pun: build atau uji konfigurasi nginx gagal. Situs tidak berubah.\n"
               + (exc.stderr or "")[-300:])
        return False
    run(COMPOSE + ["up", "-d", "--no-deps", SERVICE])
    time.sleep(8)
    problems, build = site_problems()
    for _ in range(4):                                       # nginx may need a few more seconds
        if not problems:
            break
        time.sleep(8)
        problems, build = site_problems()
    if problems:
        return roll_back("; ".join(problems))
    notify(f"GEOSTEVIA deploy frontend BERHASIL ({sha[:8]}, build {build}).\nPenguatan nginx dan pemberitahuan versi baru aktif. "
           f"Halaman, /version.json, API health, dan header HSTS lolos. Mapper perlu memuat ulang halaman sekali agar memakai kode baru.")
    log("deploy ok")
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Deploy the frontend at a commit, with a config test and a rollback")
    ap.add_argument("--sha", required=True, help="the full 40-character commit to deploy")
    ap.add_argument("--dry", action="store_true", help="show the plan and change nothing")
    ap.add_argument("--cron-marker", default=None, help="text that identifies this job's crontab line, removed when it has run")
    args = ap.parse_args()
    if len(args.sha) != 40:
        sys.exit("--sha harus 40 karakter")
    ok = False
    try:
        ok = deploy(args.sha, args.dry)
    except Exception as exc:
        log(f"deploy error: {type(exc).__name__}: {exc}")
        notify(f"GEOSTEVIA deploy frontend GAGAL di tengah jalan: {type(exc).__name__}: {str(exc)[:300]}. Periksa situs.")
    finally:
        if not args.dry:
            remove_own_cron_line(args.cron_marker)
    sys.exit(0 if ok else 1)
