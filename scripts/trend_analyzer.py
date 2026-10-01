# scripts/trend_analyzer.py
"""对比多次 analyzed_*.csv，生成趋势报告。"""
import logging
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOG_FORMAT, LOG_LEVEL, PROCESSED_DATA_DIR, get_timestamp

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class TrendAnalyzer:
    def __init__(self, data_dir=None):
        self.data_dir = data_dir or PROCESSED_DATA_DIR

    def _files(self):
        return sorted(
            os.path.join(self.data_dir, name)
            for name in os.listdir(self.data_dir)
            if name.startswith("analyzed_") and name.endswith(".csv")
        )

    def generate_trend_report(self):
        files = self._files()
        if not files:
            logger.error("没有分析结果，请先运行 analyzer.py 或 main.py")
            return None
        frames = []
        for path in files:
            frame = pd.read_csv(path)
            frame["snapshot"] = os.path.basename(path)
            frames.append(frame)
        latest = frames[-1]
        rows = []
        if len(frames) == 1:
            logger.info("只有一份快照，输出当前排名基线")
            for _, row in latest.iterrows():
                rows.append({
                    "video_id": row.get("video_id"),
                    "title": row.get("title"),
                    "channel": row.get("channel"),
                    "region": row.get("region"),
                    "latest_rank": row.get("rank"),
                    "previous_rank": None,
                    "rank_change": None,
                    "latest_score": row.get("popularity_score"),
                    "status": "baseline",
                })
        else:
            previous = frames[-2]
            prev_rank = {
                str(row["video_id"]): row for _, row in previous.iterrows()
            }
            seen = set()
            for _, row in latest.iterrows():
                video_id = str(row.get("video_id"))
                seen.add(video_id)
                old = prev_rank.get(video_id)
                previous_rank = None if old is None else old.get("rank")
                change = None
                status = "new"
                if previous_rank is not None and pd.notna(previous_rank):
                    change = float(previous_rank) - float(row.get("rank"))
                    status = "up" if change > 0 else "down" if change < 0 else "same"
                rows.append({
                    "video_id": video_id,
                    "title": row.get("title"),
                    "channel": row.get("channel"),
                    "region": row.get("region"),
                    "latest_rank": row.get("rank"),
                    "previous_rank": previous_rank,
                    "rank_change": change,
                    "latest_score": row.get("popularity_score"),
                    "previous_score": None if old is None else old.get("popularity_score"),
                    "status": status,
                })
            for video_id, old in prev_rank.items():
                if video_id not in seen:
                    rows.append({
                        "video_id": video_id,
                        "title": old.get("title"),
                        "channel": old.get("channel"),
                        "region": old.get("region"),
                        "latest_rank": None,
                        "previous_rank": old.get("rank"),
                        "rank_change": None,
                        "latest_score": None,
                        "previous_score": old.get("popularity_score"),
                        "status": "dropped",
                    })
        report = pd.DataFrame(rows)
        stamp = get_timestamp()
        stamped = os.path.join(self.data_dir, f"trend_report_{stamp}.csv")
        stable = os.path.join(self.data_dir, "trend_analysis.csv")
        report.to_csv(stamped, index=False, encoding="utf-8-sig")
        report.to_csv(stable, index=False, encoding="utf-8-sig")
        new_count = int((report["status"] == "new").sum()) if "status" in report else 0
        logger.info(
            "趋势报告已写入 %s（快照 %s 份，新上榜 %s）",
            stable,
            len(files),
            new_count,
        )
        return report


def main():
    analyzer = TrendAnalyzer()
    report = analyzer.generate_trend_report()
    if report is not None:
        print(report["status"].value_counts().to_string())


if __name__ == "__main__":
    main()
