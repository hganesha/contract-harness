"""End-to-end and unit tests for the harness (run: python -m unittest discover -s tests)."""
from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

from harness.config import load_config
from harness.pipeline import run_pipeline
from harness.utils import parse_ts_value, singularize, name_similarity, strip_comments
from harness.align.diff import fallback_field_match

ROOT = Path(__file__).resolve().parent.parent


class HarnessEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = ROOT / "outputs-test"
        if cls.out.exists():
            shutil.rmtree(cls.out)
        config = load_config(str(ROOT / "harness.config.json"), {"output_dir": str(cls.out)})
        cls.result, cls.stats = run_pipeline(config)

    def test_inventory_discovery(self):
        self.assertGreaterEqual(self.stats["ui_contracts"], 4)
        self.assertEqual(self.stats["mock_datasets"], 1)
        self.assertEqual(self.stats["api_calls"], 2)  # two supabase call sites
        self.assertGreaterEqual(self.stats["components"], 4)

    def test_order_alignment_detects_known_mismatches(self):
        order = next(a for a in self.result.alignments if a.target_entity == "Order")
        pairs = {(m.ui_field, m.target_field): m.status for m in order.field_mappings}
        self.assertEqual(pairs.get(("id", "orderId")), "FIELD_RENAME")
        self.assertEqual(pairs.get(("items", "lineItems")), "FIELD_RENAME")
        self.assertIn(pairs.get(("status", "status")),
                      ("ENUM_MISMATCH", "ENUM_NOT_ENFORCED"))
        self.assertEqual(pairs.get(("—", "amounts")), "REQUIRED_MISSING")
        self.assertIn(("total", "—"), pairs)  # dummy-only field

    def test_line_item_renames(self):
        item = next(a for a in self.result.alignments if a.target_entity == "OrderLineItem")
        pairs = {(m.ui_field, m.target_field): m.status for m in item.field_mappings}
        self.assertEqual(pairs.get(("qty", "quantity")), "FIELD_RENAME")
        self.assertEqual(pairs.get(("price", "unitPrice")), "FIELD_RENAME")
        self.assertEqual(pairs.get(("id", "lineId")), "FIELD_RENAME")
        self.assertEqual(pairs.get(("—", "sku")), "REQUIRED_MISSING")

    def test_unmatched_entities_and_rule_gaps(self):
        self.assertIn("Customer", self.result.unmatched_target)
        self.assertIn("OrderAmounts", self.result.unmatched_target)
        gap_rules = {
            f.rule_ids[0] for f in
            [f for al in self.result.alignments for f in al.findings]
            if f.code == "RULE_FIELD_GAP" and f.rule_ids
        }
        self.assertIn("BR-003", gap_rules)
        self.assertIn("BR-005", gap_rules)

    def test_specs_and_plan_integrity(self):
        rule_specs = [s for s in self.result.specs if s.rule_ids]
        self.assertEqual({s.rule_ids[0] for s in rule_specs},
                         {f"BR-00{i}" for i in range(1, 6)})
        # plan: every non-freeze task depends on something; ids are stable
        ids = {t.task_id for t in self.result.plan}
        for task in self.result.plan:
            for dep in task.depends_on:
                self.assertIn(dep, ids)
        self.assertGreater(len(self.result.plan), 7)
        # cleanup + verification phases exist
        phases = {t.phase for t in self.result.plan}
        self.assertIn("06-cleanup", phases)
        self.assertIn("07-verification", phases)

    def test_artifacts_written(self):
        for name in (
            "01-inventory.json", "02-current-contracts.md", "03-alignment-matrix.md",
            "05-migration-plan.md", "05-tasks.json", "06-traceability-matrix.md",
            "04-specs/index.md", "pipeline-result.json",
        ):
            self.assertTrue((self.out / name).exists(), name)
        # JSON artifacts are valid JSON
        for name in ("05-tasks.json", "pipeline-result.json"):
            json.loads((self.out / name).read_text())


class UnitTests(unittest.TestCase):
    def test_singularize(self):
        self.assertEqual(singularize("orders"), "order")
        self.assertEqual(singularize("categories"), "category")
        self.assertEqual(singularize("items"), "item")

    def test_name_similarity(self):
        self.assertEqual(name_similarity("OrderItem", "order-item"), 1.0)
        self.assertGreater(name_similarity("OrderItem", "OrderLineItem"), 0.5)

    def test_parse_ts_value(self):
        val, _ = parse_ts_value('[{ "a": 1 }, { b: "x" }]')
        self.assertEqual(val[0]["a"], 1)
        val2, _ = parse_ts_value("'pending'")
        self.assertEqual(val2, "pending")
        val3, _ = parse_ts_value("12.5")
        self.assertEqual(val3, 12.5)

    def test_strip_comments_preserves_strings(self):
        src = 'const x = "// not a comment"; // real comment\n'
        self.assertIn('"// not a comment"', strip_comments(src))
        self.assertNotIn("real comment", strip_comments(src))

    def test_fallback_field_match(self):
        self.assertTrue(fallback_field_match("qty", "quantity"))
        self.assertTrue(fallback_field_match("id", "orderId"))
        self.assertTrue(fallback_field_match("price", "unitPrice"))
        self.assertFalse(fallback_field_match("notes", "placedAt"))


if __name__ == "__main__":
    unittest.main()
