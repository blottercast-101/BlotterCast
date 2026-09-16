import os
import re
import unittest
from app import create_app


class TestSettlementMetricsAndDropdown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.html_path = os.path.join(cls.app.root_path, "..", "frontend", "settlement.html")
        with open(cls.html_path, "r", encoding="utf-8") as f:
            cls.html = f.read()

    def test_metric_card_titles_and_ids(self):
        # Card 1: Total Cases -> #totalSettlementCases
        self.assertIn('id="totalSettlementCases"', self.html)
        self.assertIn('>Total Cases</span>', self.html)

        # Card 2: Pending -> #pendingSettlementCases
        self.assertIn('id="pendingSettlementCases"', self.html)
        self.assertIn('>Pending</span>', self.html)

        # Card 3: Complied -> #compliedSettlementCases
        self.assertIn('id="compliedSettlementCases"', self.html)
        self.assertIn('>Complied</span>', self.html)

        # Card 4: Not Complied -> #notCompliedSettlementCases
        self.assertIn('id="notCompliedSettlementCases"', self.html)
        self.assertIn('>Not Complied</span>', self.html)

    def test_subtitles_removed_from_metric_cards(self):
        subtitles_to_check = [
            "scheduled hearings & cases",
            "scheduled hearings &amp; cases",
            "under active conciliation",
            "compliance fulfilled",
            "non-compliance / CFA issued",
        ]
        for sub in subtitles_to_check:
            self.assertNotIn(sub, self.html, f"Subtitle '{sub}' should be removed from settlement cards")

    def test_action_taken_dropdown_options(self):
        # Must contain official modes
        self.assertIn('<option value="" disabled selected>-Select-</option>', self.html)
        self.assertIn('<option value="Mediation (M)">Mediation (M)</option>', self.html)
        self.assertIn('<option value="Conciliation (C)">Conciliation (C)</option>', self.html)
        self.assertIn('<option value="Arbitration (A)">Arbitration (A)</option>', self.html)

        # Must not contain invalid / test options
        self.assertNotIn('value="w EP"', self.html)
        self.assertNotIn('>w EP<', self.html)
        self.assertNotIn('value="C46+"', self.html)
        self.assertNotIn('>C46+<', self.html)

    def test_metric_calculation_logic_present(self):
        self.assertIn("function updateSettlementMetrics()", self.html)
        self.assertIn("totalSettlementCases", self.html)
        self.assertIn("pendingSettlementCases", self.html)
        self.assertIn("compliedSettlementCases", self.html)
        self.assertIn("notCompliedSettlementCases", self.html)
        # Check status matching for pending/ongoing and complied/settled and not complied/repudiated/elevated
        self.assertIn("'pending'", self.html)
        self.assertIn("'ongoing'", self.html)
        self.assertIn("'complied'", self.html)
        self.assertIn("'settled'", self.html)
        self.assertIn("'not complied'", self.html)
        self.assertIn("'repudiated'", self.html)
        self.assertIn("'elevated'", self.html)


if __name__ == "__main__":
    unittest.main()
