# scripts/predictors.py
"""用当前热度公式外推 48 小时后的分数。"""
import argparse
import json
import logging
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOG_FORMAT, LOG_LEVEL, POPULARITY_WEIGHTS, PROCESSED_DATA_DIR, RAW_DATA_DIR
from scripts.analyzer import PopularityAnalyzer
from scripts.utils import resolve_hours

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class PopularityPredictor:
    def __init__(self, weights=None):
        self.analyzer = PopularityAnalyzer(weights)

    def _lookup(self, video_id):
        csv_files = sorted(
            os.path.join(PROCESSED_DATA_DIR, name)
            for name in os.listdir(PROCESSED_DATA_DIR)
            if name.startswith("analyzed_") and name.endswith(".csv")
        )
        for path in reversed(csv_files):
            frame = pd.read_csv(path)
            hit = frame[frame["video_id"].astype(str) == str(video_id)]
            if not hit.empty:
                return hit.iloc[0].to_dict()
        raw_files = sorted(
            os.path.join(RAW_DATA_DIR, name)
            for name in os.listdir(RAW_DATA_DIR)
            if name.endswith(".json")
        )
        for path in reversed(raw_files):
            with open(path, "r", encoding="utf-8") as handle:
                for item in json.load(handle):
                    if str(item.get("video_id")) == str(video_id):
                        return item
        return None

    def _fetch(self, video_id):
        from scripts.scraper import YouTubeTrendingScraper
        scraper = YouTubeTrendingScraper()
        video = {
            "video_id": video_id,
            "title": "",
            "channel": "",
            "views": 0,
            "likes": 0,
            "comments": 0,
            "region": "US",
            "publish_time": "",
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }
        scraper.enrich_videos([video])
        if not video.get("views"):
            return None
        return video

    def predict_48h_later(self, video_id):
        video = self._lookup(video_id)
        if video is None:
            logger.info("本地没有 %s，改为在线读取", video_id)
            video = self._fetch(video_id)
        if not video:
            logger.error("无法预测，找不到视频 %s", video_id)
            return None
        hours = resolve_hours(video)
        base = float(video.get("base_score") or self.analyzer.base_score(video))
        decay = self.analyzer.weights["time_decay"]
        current = base / (hours ** decay) if hours else 0
        future_hours = hours + 48
        future = base / (future_hours ** decay) if future_hours else 0
        result = {
            "video_id": video_id,
            "title": video.get("title"),
            "channel": video.get("channel"),
            "hours_since_upload": hours,
            "current_score": current,
            "predicted_score_48h": future,
        }
        logger.info(
            "%s 当前热度 %.1f，48 小时后预测 %.1f",
            video_id,
            current,
            future,
        )
        return result


def main():
    parser = argparse.ArgumentParser(description="预测视频 48 小时后的热度")
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--log-level", default=None)
    args = parser.parse_args()
    if args.log_level:
        logging.getLogger().setLevel(args.log_level.upper())
    result = PopularityPredictor().predict_48h_later(args.video_id)
    if result is None:
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
