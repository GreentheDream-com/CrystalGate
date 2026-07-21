# Copyright © 2026 Derrick Covington.
# Published through Green The Dream Research Lab.
#
# Licensed under the PolyForm Noncommercial License 1.0.0.
# License: https://polyformproject.org/licenses/noncommercial/1.0.0
# Commercial licensing: derrick@greenthedream.com
#
# Required Notice: Copyright © 2026 Derrick Covington.
# Required Notice: Published through Green The Dream Research Lab.

import unittest

import gatefinder_demo


class MinimalGateFinderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema, cls.reports = gatefinder_demo.run(
            gatefinder_demo.DEFAULT_SCHEMA,
            gatefinder_demo.DEFAULT_CLAIMS,
        )
        cls.by_id = {report["claim_id"]: report for report in cls.reports}

    def test_artifact_population(self):
        self.assertEqual(len(self.schema["translators"]), 8)
        self.assertEqual(len(self.reports), 6)

    def test_verdict_distribution(self):
        counts = {}
        for report in self.reports:
            counts[report["verdict"]] = counts.get(report["verdict"], 0) + 1
        self.assertEqual(
            counts,
            {"accepted": 2, "rerouted": 1, "rejected": 2, "underdetermined": 1},
        )

    def test_reroute_removes_implicit_cast(self):
        report = self.by_id["rerouted_implicit_cast"]
        self.assertEqual(report["verdict"], "rerouted")
        self.assertNotIn("implicit.scalar_to_pi_phase", report["selected_route_ids"])
        self.assertIn("scalar.phase_normalize", report["selected_route_ids"])
        self.assertGreaterEqual(len(report["searched_routes"]), 2)

    def test_missing_evidence_is_not_passage(self):
        report = self.by_id["underdetermined_missing_observable"]
        self.assertEqual(report["verdict"], "underdetermined")
        self.assertIn("observable.response_declared", report["unresolved_obligations"])

    def test_soft_pass_is_reported_as_evaluated(self):
        report = self.by_id["accepted_large_soft_residual"]
        certificate = next(
            item
            for item in report["certificates"]
            if item["gate_id"] == "observable.phase_mismatch"
        )
        self.assertEqual(certificate["status"], "pass")
        self.assertEqual(certificate["report_status"], "evaluated")
        self.assertEqual(certificate["residual"], 25.0)
        self.assertEqual(report["verdict"], "accepted")

    def test_singular_boundary_is_hard_failure(self):
        report = self.by_id["rejected_singular_matrix"]
        self.assertEqual(report["verdict"], "rejected")
        self.assertTrue(
            {"window.scalar_nonzero", "window.argument_nonzero"}
            & set(report["failed_obligations"])
        )


if __name__ == "__main__":
    unittest.main()
