import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("deploy_frontend", Path(__file__).resolve().parents[1] / "scripts" / "deploy_frontend.py")
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


def test_the_job_removes_only_its_own_cron_line():
    crontab = ("5 0,6,12 * * * python3 monitor.py\n"
               "0 17 24 10 * python3 deploy_frontend.py --sha abc  # geostevia-deploy-once\n"
               "* * * * * flock -n lock python3 monitor.py --poll\n")
    out = deploy.strip_cron_line(crontab, "geostevia-deploy-once")
    assert "deploy_frontend" not in out and "monitor.py --poll" in out and "monitor.py\n" in out
    assert out.endswith("\n") and out.count("\n") == 2


def test_nothing_is_removed_without_a_marker_match():
    crontab = "5 0 * * * python3 monitor.py\n"
    assert deploy.strip_cron_line(crontab, "geostevia-deploy-once") == crontab
