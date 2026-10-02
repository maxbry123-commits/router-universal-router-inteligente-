import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import launch


class LaunchTests(TestCase):
    def test_no_paid_job_for_empty_queue(self):
        with patch.object(launch, "GitHubStore") as store_type, patch.object(launch, "hf") as hf:
            store = store_type.return_value
            store.read.return_value = None
            store.requests.return_value = []
            with self.assertRaisesRegex(RuntimeError, "NO_TASKS_NO_PAID_JOB"):
                launch.launch("owner/repo", "feature", "gpt-4.1-mini", "g", "o", "h", "owner")
            hf.assert_not_called()

    def test_controlled_stop_cannot_relaunch(self):
        with patch.object(launch, "GitHubStore") as store_type, patch.object(launch, "hf") as hf:
            store_type.return_value.read.return_value = '{"state":"STOPPED_BY_DIRECTOR"}'
            with self.assertRaisesRegex(RuntimeError, "STOPPED_BY_DIRECTOR"):
                launch.launch("owner/repo", "feature", "gpt-4.1-mini", "g", "o", "h", "owner")
            hf.assert_not_called()

    def test_no_second_running_supervisor(self):
        with patch.object(launch, "GitHubStore") as store_type, patch.object(launch, "hf") as hf:
            store = store_type.return_value
            store.read.return_value = None
            store.requests.return_value = ["req-001"]
            store.ref.return_value = {"object": {"sha": "abc"}}
            hf.return_value = [{"status": {"stage": "RUNNING"}}]
            with self.assertRaisesRegex(RuntimeError, "SUPERVISOR_ALREADY_RUNNING"):
                launch.launch("owner/repo", "feature", "gpt-4.1-mini", "g", "o", "h", "owner")
            self.assertEqual(hf.call_count, 1)

    def test_model_is_not_substituted(self):
        with patch.object(launch, "hf") as hf:
            with self.assertRaisesRegex(ValueError, "ONLY_OPENAI_MODELS_ALLOWED"):
                launch.launch("owner/repo", "feature", "deepseek-ai/DeepSeek", "g", "o", "h", "owner")
            hf.assert_not_called()
