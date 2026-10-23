import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("daily_monitor", Path(__file__).resolve().parents[1] / "scripts" / "daily_monitor.py")
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


def update(uid, chat, text):
    return {"update_id": uid, "message": {"chat": {"id": chat}, "text": text}}


def press(uid, chat, data):
    return {"update_id": uid, "callback_query": {"id": f"cb{uid}", "data": data, "message": {"chat": {"id": chat}}}}


def test_only_events_from_the_authorised_chat_are_picked_but_every_update_is_acknowledged():
    updates = [update(10, 111, "/periksa"), update(11, 999, "/periksa 72"), update(12, 111, "halo"), update(13, 111, "/bantuan"),
               press(14, 111, "fx:g:22"), press(15, 999, "fx:g:22")]
    events, nxt = monitor.pick_events(updates, "111")
    assert events == [("command", "/periksa"), ("command", "/bantuan"), ("callback", {"id": "cb14", "data": "fx:g:22"})] and nxt == 16


def test_nothing_waiting_means_no_offset_change():
    assert monitor.pick_events([], "111") == ([], None)


def test_periksa_takes_an_optional_number_of_hours_within_limits():
    assert monitor.parse_command("/periksa") == ("report", 8)
    assert monitor.parse_command("/periksa 24") == ("report", 24)
    assert monitor.parse_command("/periksa@geostevia_bot 5") == ("report", 5)
    assert monitor.parse_command("/periksa 99999") == ("report", 168)
    assert monitor.parse_command("/periksa 0") == ("report", 1)
    assert monitor.parse_command("/periksa banyak") == ("report", 8)
    assert monitor.parse_command("/start") == ("help", None)


def test_format_ops_shows_the_last_operations_with_counts_and_age():
    ops = [{"op": "load_server", "ago": 900}, {"op": "undo", "ago": 30}, {"op": "edit_vertices", "n": 5, "ago": 7}, {"op": "split_poly", "ago": 1}]
    assert monitor.format_ops(ops, limit=3) == "undo (30s) > edit_vertices x5 (7s) > split_poly (1s)"
    assert monitor.format_ops(None) == ""


def test_fix_takes_an_optional_grid_and_other_text_is_help():
    assert monitor.parse_command("/fix") == ("fix", "")
    assert monitor.parse_command("/fix 013_2022") == ("fix", "013_2022")
    assert monitor.parse_command("/fix@geostevia_bot 013") == ("fix", "013")


def test_grid_pattern_pads_bare_numbers_and_refuses_anything_that_is_not_a_plain_code():
    assert monitor.grid_pattern("13") == "SB_GRID_013_%"
    assert monitor.grid_pattern("013_2022") == "%013_2022%"
    assert monitor.grid_pattern("sb_grid_22_2025") == "%SB_GRID_22_2025%"
    for bad in ("", "a'; drop table x;--", "13 or 1=1", "x" * 31, "%"):
        assert monitor.grid_pattern(bad) is None


def test_the_bot_can_only_ever_run_the_repair_scripts_as_a_dry_run():
    for kind in monitor.FIX_SCRIPTS:
        cmds = monitor.fix_commands(kind, 22)
        assert all("--apply" not in part for cmd in cmds for part in cmd)
        assert "22" in cmds[1]
    assert monitor.fix_commands("o", "129")[1][-1] == "129"
    try:
        monitor.fix_commands("o", "1; rm -rf /")
        raise AssertionError("a grid id must be a number")
    except ValueError:
        pass


def test_fix_summary_keeps_the_numbers_and_trims_long_cluster_lists():
    dedupe = "\n".join(["grid 22 SB_GRID_022_2025 | last mapper save x (idle 1:00:00) | mode DRY RUN"]
                       + [f"cluster of 2: keep #{n} (class 1, 10 ha, created 2026-10-22 07:32:17.790069); delete #{n - 1}(class 1, created 07:04:39)" for n in range(7)]
                       + ["polygons in grid: 1488 | large polygons (>= 10 ha): 416 | stale copies to delete: 7", "dry run: nothing written"])
    out = monitor.summarize_fix("d", dedupe)
    assert "mode DRY RUN" in out and "stale copies to delete: 7" in out and "dan 2 kluster lain" in out
    assert "created" not in out.split("\n")[1] and "nothing written" not in out
    assert monitor.summarize_fix("o", "noise only").startswith("(tidak ada keluaran)")
