import sys
from pathlib import Path
from unittest import TestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from github_store import GitHubStore


class GitHubStoreTests(TestCase):
    def test_checkpoint_commits_code_and_state_together_and_reads_back(self):
        store = GitHubStore("owner/repo", "fake-token")
        state = {"head": "parent", "content": {}}

        def request(method, route, data=None, missing=False):
            if route.startswith(("/git/ref/heads/", "/git/refs/heads/")):
                if method == "PATCH":
                    state["head"] = data["sha"]
                return {"object": {"sha": state["head"]}}
            if method == "GET" and route.startswith("/git/commits/"):
                return {"tree": {"sha": "old-tree"}}
            if route == "/git/blobs":
                return {"sha": "blob"}
            if route == "/git/trees":
                self.assertEqual(len(data["tree"]), 2)
                return {"sha": "tree"}
            if route == "/git/commits":
                self.assertEqual(data["parents"], ["parent"])
                return {"sha": "new-head"}
            raise AssertionError((method, route))

        store.request = request
        store.read = lambda name, ref: {"src/a.py": "code", "output/state.json": "state"}[name]
        files = {"src/a.py": "code", "output/state.json": "state"}
        self.assertEqual(store.checkpoint("branch", "parent", files, "checkpoint"), "new-head")
        self.assertEqual(state["head"], "new-head")

    def test_concurrent_ref_rejected_without_writing(self):
        store = GitHubStore("owner/repo", "fake-token")
        store.request = lambda *args, **kwargs: {"object": {"sha": "other"}}
        with self.assertRaisesRegex(RuntimeError, "CHECKPOINT_CONCURRENT_UPDATE"):
            store.checkpoint("branch", "parent", {"src/a": "hi"}, "checkpoint")

    def test_wrong_readback_blocks(self):
        store = GitHubStore("owner/repo", "fake-token")
        store.request = lambda method, route, data=None, missing=False: (
            {"object": {"sha": "parent"}} if route.startswith("/git/ref/heads/") else
            {"tree": {"sha": "tree"}} if method == "GET" else {"sha": "new-head"})
        store.read = lambda *_: "wrong"
        with self.assertRaises(RuntimeError):
            store.checkpoint("branch", "parent", {"src/a": "correct"}, "checkpoint")
