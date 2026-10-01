# scripts/analyzer.py
import argparse
import json
import logging
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    EXPORT_FORMATS,
    LOG_FORMAT,
    LOG_LEVEL,
    POPULARITY_WEIGHTS,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    get_timestamp,
)
from scripts.utils import resolve_hours

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class PopularityAnalyzer:
    def __init__(self, weights=None):
        self.weights = dict(weights or POPULARITY_WEIGHTS)

    def calculate_popularity_score(self, video):
        """
        热度分数 = 基础分数 / 时间衰减因子
        基础分数 = views * views_weight + comments * comments_weight + likes * likes_weight
        时间衰减 = hours ^ time_decay
        """
        try:
            views = float(video.get("views", 0) or 0)
            comments = float(video.get("comments", 0) or 0)
            likes = float(video.get("likes", 0) or 0)
            hours = resolve_hours(video)
            base_score = (
                views * self.weights["views"]
                + comments * self.weights["comments"]
                + likes * self.weights["likes"]
            )
            decay = hours ** self.weights["time_decay"]
            if decay <= 0:
                return 0.0
            return base_score / decay
        except Exception as exc:
            logger.debug("计算热度分数失败: %s", exc)
            return 0.0

    def base_score(self, video):
        views = float(video.get("views", 0) or 0)
        comments = float(video.get("comments", 0) or 0)
        likes = float(video.get("likes", 0) or 0)
        return (
            views * self.weights["views"]
            + comments * self.weights["comments"]
            + likes * self.weights["likes"]
        )

    def analyze(self, videos_list):
        logger.info("开始分析 %s 个视频...", len(videos_list))
        if not videos_list:
            return pd.DataFrame(columns=[
                "rank", "title", "channel", "region", "views", "comments", "likes",
                "publish_time", "popularity_score", "url", "video_id", "scraped_at",
            ])
        df = pd.DataFrame(videos_list)
        for column in ("views", "comments", "likes"):
            if column not in df.columns:
                df[column] = 0
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)
        df["hours_since_upload"] = df.apply(resolve_hours, axis=1)
        df["base_score"] = df.apply(self.base_score, axis=1)
        df["popularity_score"] = df.apply(self.calculate_popularity_score, axis=1)
        df = df.sort_values("popularity_score", ascending=False).reset_index(drop=True)
        df["rank"] = range(1, len(df) + 1)
        columns_order = [
            "rank", "title", "channel", "region", "views", "comments", "likes",
            "publish_time", "publish_date", "hours_since_upload", "base_score",
            "popularity_score", "url", "video_id", "source", "length_seconds", "scraped_at",
        ]
        existing = [col for col in columns_order if col in df.columns]
        extras = [col for col in df.columns if col not in existing]
        df = df[existing + extras]
        logger.info("分析完成，共 %s 个视频", len(df))
        return df

    def get_top_videos(self, df, n=10):
        return df.head(n)

    def get_by_region(self, df, region):
        return df[df["region"] == region].head(10)

    def get_statistics(self, df):
        if df is None or len(df) == 0:
            return {
                "total_videos": 0,
                "regions": 0,
                "avg_views": 0,
                "avg_score": 0,
                "top_channel": "N/A",
            }
        channels = df["channel"].fillna("").astype(str)
        channels = channels[channels.str.len() > 0]
        top_channel = channels.value_counts().index[0] if len(channels) else "N/A"
        return {
            "total_videos": int(len(df)),
            "regions": int(df["region"].nunique()) if "region" in df.columns else 0,
            "avg_views": float(df["views"].mean()),
            "avg_score": float(df["popularity_score"].mean()),
            "top_channel": top_channel,
        }


def export_dataframe(df, stem):
    """Write csv / json / xlsx according to EXPORT_FORMATS. Returns path map."""
    paths = {}
    if "csv" in EXPORT_FORMATS:
        path = os.path.join(PROCESSED_DATA_DIR, f"{stem}.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        paths["csv"] = path
    if "json" in EXPORT_FORMATS:
        path = os.path.join(PROCESSED_DATA_DIR, f"{stem}.json")
        df.to_json(path, orient="records", force_ascii=False, indent=2)
        paths["json"] = path
    if "xlsx" in EXPORT_FORMATS:
        path = os.path.join(PROCESSED_DATA_DIR, f"{stem}.xlsx")
        df.to_excel(path, index=False, engine="openpyxl")
        paths["xlsx"] = path
    return paths


def load_latest_raw():
    raw_files = sorted(f for f in os.listdir(RAW_DATA_DIR) if f.endswith(".json"))
    if not raw_files:
        return None, None
    latest = os.path.join(RAW_DATA_DIR, raw_files[-1])
    with open(latest, "r", encoding="utf-8") as handle:
        return latest, json.load(handle)


def main():
    parser = argparse.ArgumentParser(description="分析已抓取的热榜数据")
    parser.add_argument("--log-level", default=None)
    args = parser.parse_args()
    if args.log_level:
        logging.getLogger().setLevel(args.log_level.upper())

    latest_raw_file, videos = load_latest_raw()
    if not videos:
        logger.error("未找到原始数据文件，请先运行 scraper.py")
        return None
    logger.info("读取数据文件: %s", latest_raw_file)
    analyzer = PopularityAnalyzer()
    df_analyzed = analyzer.analyze(videos)
    paths = export_dataframe(df_analyzed, f"analyzed_{get_timestamp()}")
    for kind, path in paths.items():
        logger.info("分析结果已保存 (%s): %s", kind, path)
    stats = analyzer.get_statistics(df_analyzed)
    logger.info("统计信息: %s", stats)
    columns = [c for c in ["rank", "title", "channel", "views", "popularity_score", "region"] if c in df_analyzed.columns]
    logger.info("\n=== TOP 10 热榜视频 ===")
    print(df_analyzed[columns].head(10).to_string(index=False))
    return df_analyzed


if __name__ == "__main__":
    main()
