"""Read-only ECC source integrity. The 311 entries are inventory, NOT 311 executable handlers."""
import hashlib
import json
import unittest
from pathlib import Path

LOOP = Path(__file__).resolve().parents[1]
ROOT = LOOP.parents[1] / "workflow-loop-code-yaiwes" / "skills" / "workflow-loop-yaiwes" / "ECC" / "skills"

class ECCSourceInventory(unittest.TestCase):
    def test_311_source_index(self):
        data = json.loads((LOOP / "config" / "ecc_source_inventory.json").read_text(encoding="utf8"))
        self.assertEqual(data["skill_count"], 311)
        self.assertEqual(len(data["sources"]), 311)
        self.assertEqual(len({x["path"] for x in data["sources"]}), 311)
        self.assertEqual(data["kind"], "INDEX_ONLY_NOT_EXECUTION")

    def test_five_literal_source_sha256(self):
        data = json.loads((LOOP / "config" / "ecc_source_inventory.json").read_text(encoding="utf8"))
        for item in data["verified_source_sha256_first_batch"]:
            path = ROOT / item["name"] / "SKILL.md"
            raw = path.read_bytes()
            with self.subTest(skill=item["name"]):
                self.assertEqual(len(raw),item["bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(),item["source_sha256"])

if __name__ == "__main__":
    unittest.main()
