import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.scraper import YouTubeTrendingScraper, _comment_count


class ParseRendererTest(unittest.TestCase):
    def test_grid_video_renderer(self):
        scraper = YouTubeTrendingScraper()
        renderer = {
            "videoId": "abcdefghijk",
            "title": {"runs": [{"text": "Hello"}]},
            "longBylineText": {"runs": [{"text": "Channel A"}]},
            "viewCountText": {"simpleText": "1.5M views"},
            "publishedTimeText": {"simpleText": "4 hours ago"},
        }
        video = scraper._parse_renderer(renderer, "US", "test")
        self.assertEqual(video["video_id"], "abcdefghijk")
        self.assertEqual(video["title"], "Hello")
        self.assertEqual(video["channel"], "Channel A")
        self.assertEqual(video["views"], 1_500_000)
        self.assertEqual(video["region"], "US")

    def test_comment_count(self):
        payload = {
            "engagementPanels": [{
                "engagementPanelSectionListRenderer": {
                    "header": {
                        "engagementPanelTitleHeaderRenderer": {
                            "contextualInfo": {"runs": [{"text": "2.4M"}]}
                        }
                    }
                }
            }]
        }
        self.assertEqual(_comment_count(payload), 2_400_000)

    def test_proxy_rotation_cycle(self):
        scraper = YouTubeTrendingScraper(use_proxy=True)
        scraper.proxy_list = ["http://p1:1", "http://p2:2"]
        first = scraper._next_proxy()
        second = scraper._next_proxy()
        third = scraper._next_proxy()
        self.assertEqual(first["http"], "http://p1:1")
        self.assertEqual(second["http"], "http://p2:2")
        self.assertEqual(third["http"], "http://p1:1")


if __name__ == "__main__":
    unittest.main()
