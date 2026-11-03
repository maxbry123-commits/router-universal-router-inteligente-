import importlib.util
import tempfile
import unittest
from pathlib import Path

LOOP_ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = LOOP_ROOT.parent / "wachdog" / "nct_addons" / "watchdog48" / "core.py"
spec = importlib.util.spec_from_file_location("watchdog48_cycle_core", CORE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("No se pudo cargar el núcleo Watchdog48")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


class WatchdogCycleTests(unittest.TestCase):
    def test_ping_cycle_create_heartbeat_tick_control_cancel(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = core.WatchStore(Path(tmp) / "watchdog.db")
            watch = store.create({
                "name": "ping watchdog cycle test",
                "target_type": "heartbeat",
                "target_id": "ping-cycle-test",
                "duration_minutes": 10,
                "interval_seconds": 5,
                "stale_seconds": 15,
                "max_alerts": 3,
            })
            wid = watch["id"]

            beat = store.heartbeat(wid, "ping-1")
            self.assertEqual(beat["last_progress"], "ping-1")

            checked = store.tick()
            self.assertEqual(len(checked), 1)
            self.assertEqual(checked[0]["watch_id"], wid)
            self.assertEqual(checked[0]["status"], "active")

            self.assertEqual(store.control(wid, "pause")["status"], "paused")
            self.assertEqual(store.control(wid, "resume")["status"], "active")
            self.assertEqual(store.control(wid, "cancel")["status"], "cancelled")

            events = [event["event"] for event in store.events(wid)]
            self.assertEqual(events, [
                "watch.created",
                "watch.heartbeat",
                "watch.checked",
                "watch.paused",
                "watch.active",
                "watch.cancelled",
            ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
