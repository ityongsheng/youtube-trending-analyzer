import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.analyzer import PopularityAnalyzer
from scripts.utils import parse_count, hours_from_relative


class PopularityFormulaTest(unittest.TestCase):
    def test_readme_example(self):
        analyzer = PopularityAnalyzer()
        video = {
            "views": 1_000_000,
            "comments": 5_000,
            "likes": 20_000,
            "publish_time": "2 hours ago",
        }
        score = analyzer.calculate_popularity_score(video)
        expected = 1_008_500 / math.sqrt(2)
        self.assertAlmostEqual(score, expected, places=2)

    def test_parse_count(self):
        self.assertEqual(parse_count("1.2M views"), 1_200_000)
        self.assertEqual(parse_count("3.5万"), 35_000)
        self.assertEqual(parse_count("2.4M"), 2_400_000)
        self.assertEqual(parse_count("1,234"), 1234)
        self.assertEqual(parse_count("1,1 mil"), 1100)
        self.assertEqual(parse_count("11 mil"), 11000)
        self.assertEqual(parse_count("1,234,567 views"), 1234567)

    def test_relative_hours(self):
        self.assertEqual(hours_from_relative("2 hours ago"), 2)
        self.assertEqual(hours_from_relative("3天前"), 72)
        self.assertEqual(hours_from_relative("1 week ago"), 168)
        self.assertEqual(hours_from_relative("hace 2 días"), 48)
        self.assertEqual(hours_from_relative("2日前"), 48)
        self.assertEqual(hours_from_relative("il y a 3 jours"), 72)
        self.assertEqual(hours_from_relative("7 दिन पहले"), 168)


if __name__ == "__main__":
    unittest.main()
