import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("daily_monitor", Path(__file__).resolve().parents[1] / "scripts" / "daily_monitor.py")
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


def update(uid, chat, text):
    return {"update_id": uid, "message": {"chat": {"id": chat}, "text": text}}


def test_only_commands_from_the_authorised_chat_are_picked_but_every_update_is_acknowledged():
    updates = [update(10, 111, "/periksa"), update(11, 999, "/periksa 72"), update(12, 111, "halo"), update(13, 111, "/bantuan")]
    commands, nxt = monitor.pick_commands(updates, "111")
    assert commands == ["/periksa", "/bantuan"] and nxt == 14


def test_nothing_waiting_means_no_offset_change():
    assert monitor.pick_commands([], "111") == ([], None)


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
