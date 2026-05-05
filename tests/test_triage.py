import unittest

from kilnwatch.triage import TriageDecision, compute_triage


class TriageTests(unittest.TestCase):
    def test_ignore_when_no_kiln(self):
        result = compute_triage({"kiln_detected": False, "confidence": 0.99, "compliance_risk_score": 1.0})
        self.assertEqual(result.decision, TriageDecision.IGNORE)

    def test_json_alert_for_low_risk_kiln(self):
        result = compute_triage({"kiln_detected": True, "confidence": 0.72, "compliance_risk_score": 0.2})
        self.assertEqual(result.decision, TriageDecision.JSON_ALERT_ONLY)

    def test_crop_for_medium_risk_kiln(self):
        result = compute_triage({"kiln_detected": True, "confidence": 0.72, "compliance_risk_score": 0.6})
        self.assertEqual(result.decision, TriageDecision.CROP_OR_REVIEW)

    def test_full_downlink_for_high_confidence_high_risk(self):
        result = compute_triage({"kiln_detected": True, "confidence": 0.9, "compliance_risk_score": 0.9})
        self.assertEqual(result.decision, TriageDecision.FULL_DOWNLINK)


if __name__ == "__main__":
    unittest.main()

