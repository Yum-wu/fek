import unittest

from fek.classifier import ComplexityClassifier, band
from fek.core.types import Complexity


class TestClassifier(unittest.TestCase):
    def test_low_complexity(self):
        c = ComplexityClassifier()
        self.assertLess(c.score("What is 2+2?"), 0.33)
        self.assertEqual(c.classify("What is 2+2?"), Complexity.LOW)

    def test_high_complexity(self):
        c = ComplexityClassifier()
        hard = "Compare and debate the trade-offs of microservices versus monoliths, considering latency, cost, and team structure."
        self.assertGreaterEqual(c.score(hard), 0.66)
        self.assertEqual(c.classify(hard), Complexity.HIGH)

    def test_band_boundaries(self):
        self.assertEqual(band(0.1), Complexity.LOW)
        self.assertEqual(band(0.5), Complexity.MEDIUM)
        self.assertEqual(band(0.9), Complexity.HIGH)

    def test_score_in_range(self):
        c = ComplexityClassifier()
        for p in ["a", "x" * 500, "compare versus debate"]:
            s = c.score(p)
            self.assertGreaterEqual(s, 0.0)
            self.assertLessEqual(s, 1.0)


if __name__ == "__main__":
    unittest.main()
