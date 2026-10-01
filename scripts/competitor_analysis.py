# scripts/competitor_analysis.py
"""对比多个频道的播放量、互动率和上榜次数。"""
import argparse
import logging
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOG_FORMAT, LOG_LEVEL, PROCESSED_DATA_DIR

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def _latest_csv():
    files = sorted(
        os.path.join(PROCESSED_DATA_DIR, name)
        for name in os.listdir(PROCESSED_DATA_DIR)
        if name.startswith("analyzed_") and name.endswith(".csv")
    )
    return files[-1] if files else None


def analyze_competitors(channels, metrics, output):
    path = _latest_csv()
    if not path:
        logger.error("未找到分析结果")
        return None
    df = pd.read_csv(path)
    df["channel"] = df["channel"].fillna("").astype(str)
    rows = []
    for name in channels:
        subset = df[df["channel"].str.contains(name, case=False, regex=False)]
        views = float(subset["views"].sum()) if len(subset) else 0.0
        likes = float(subset["likes"].sum()) if len(subset) and "likes" in subset else 0.0
        comments = float(subset["comments"].sum()) if len(subset) and "comments" in subset else 0.0
        engagement = (likes + comments) / views if views else 0.0
        record = {
            "channel": name,
            "videos": int(len(subset)),
            "views": views,
            "engagement_rate": engagement,
            "upload_frequency": int(len(subset)),
            "avg_score": float(subset["popularity_score"].mean()) if len(subset) else 0.0,
        }
        rows.append(record)
    report = pd.DataFrame(rows)
    keep = ["channel"] + [metric for metric in metrics if metric in report.columns]
    # always keep videos so the file is useful even if a metric name is unknown
    if "videos" not in keep:
        keep.append("videos")
    report = report[keep].sort_values(keep[1] if len(keep) > 1 else "channel", ascending=False)
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    report.to_csv(output, index=False, encoding="utf-8-sig")
    logger.info("竞品报告: %s", output)
    print(report.to_string(index=False))
    return report


def main():
    parser = argparse.ArgumentParser(description="竞品频道对比")
    parser.add_argument("--channels", required=True, help="逗号分隔的频道名")
    parser.add_argument(
        "--metrics",
        default="views,engagement_rate,upload_frequency",
        help="views,engagement_rate,upload_frequency",
    )
    parser.add_argument("--output", default=os.path.join(PROCESSED_DATA_DIR, "competitor_report.csv"))
    parser.add_argument("--log-level", default=None)
    args = parser.parse_args()
    if args.log_level:
        logging.getLogger().setLevel(args.log_level.upper())
    channels = [part.strip() for part in args.channels.split(",") if part.strip()]
    metrics = [part.strip() for part in args.metrics.split(",") if part.strip()]
    result = analyze_competitors(channels, metrics, args.output)
    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
