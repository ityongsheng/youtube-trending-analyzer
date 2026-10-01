# scripts/channel_analyzer.py
"""频道深度分析：热度分布、上传时间、内容类型。"""
import argparse
import logging
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOG_FORMAT, LOG_LEVEL, PROCESSED_DATA_DIR

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

from scripts.visualizer import configure_matplotlib_fonts
configure_matplotlib_fonts()

_TYPE_RULES = [
    ("音乐", re.compile(r"music|song|official video|lyrics|mv|歌曲|音乐", re.I)),
    ("游戏", re.compile(r"game|gaming|minecraft|gameplay|游戏", re.I)),
    ("新闻", re.compile(r"news|headline|新闻|速报", re.I)),
    ("短视频", None),
]


def _latest_csv():
    files = sorted(
        os.path.join(PROCESSED_DATA_DIR, name)
        for name in os.listdir(PROCESSED_DATA_DIR)
        if name.startswith("analyzed_") and name.endswith(".csv")
    )
    return files[-1] if files else None


def _content_type(row):
    length = row.get("length_seconds")
    try:
        if pd.notna(length) and float(length) <= 60:
            return "短视频"
    except (TypeError, ValueError):
        pass
    title = str(row.get("title") or "")
    for label, pattern in _TYPE_RULES:
        if pattern and pattern.search(title):
            return label
    return "其他"


def _publish_bucket(row):
    hours = row.get("hours_since_upload")
    try:
        hours = float(hours)
    except (TypeError, ValueError):
        return "未知"
    if hours < 24:
        return "24小时内"
    if hours < 24 * 7:
        return "本周"
    if hours < 24 * 30:
        return "本月"
    return "更早"


def analyze_channel(channel_name, csv_path=None):
    path = csv_path or _latest_csv()
    if not path:
        logger.error("未找到分析结果，请先运行 main.py")
        return None
    df = pd.read_csv(path)
    mask = df["channel"].fillna("").astype(str).str.contains(re.escape(channel_name), case=False)
    subset = df[mask].copy()
    if subset.empty:
        logger.error("没有找到频道: %s", channel_name)
        known = df["channel"].fillna("").astype(str).value_counts().head(8)
        logger.info("热榜中出现较多的频道:\n%s", known.to_string())
        return None
    subset["content_type"] = subset.apply(_content_type, axis=1)
    subset["publish_bucket"] = subset.apply(_publish_bucket, axis=1)
    type_counts = subset["content_type"].value_counts()
    bucket_score = subset.groupby("publish_bucket")["popularity_score"].mean().sort_values(ascending=False)
    best_time = bucket_score.index[0] if len(bucket_score) else "未知"
    summary = {
        "channel": channel_name,
        "videos": int(len(subset)),
        "avg_views": float(subset["views"].mean()),
        "avg_score": float(subset["popularity_score"].mean()),
        "best_publish_bucket": best_time,
        "top_content_type": type_counts.index[0] if len(type_counts) else "其他",
    }
    safe = re.sub(r"[^\w]+", "_", channel_name, flags=re.UNICODE).strip("_") or "channel"
    out_csv = os.path.join(PROCESSED_DATA_DIR, f"channel_{safe}.csv")
    subset.to_csv(out_csv, index=False, encoding="utf-8-sig")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    subset["popularity_score"].plot(kind="hist", bins=min(10, max(len(subset), 1)), ax=axes[0], color="#4C78A8")
    axes[0].set_title("热度分布")
    axes[0].set_xlabel("热度分数")
    type_counts.plot(kind="bar", ax=axes[1], color="#F58518")
    axes[1].set_title("内容类型")
    fig.suptitle(f"频道分析: {channel_name}")
    fig.tight_layout()
    chart = os.path.join(PROCESSED_DATA_DIR, "visualizations", f"channel_{safe}.png")
    fig.savefig(chart, dpi=120, bbox_inches="tight")
    plt.close(fig)
    logger.info("频道 %s: %s", channel_name, summary)
    logger.info("明细: %s", out_csv)
    logger.info("图表: %s", chart)
    logger.info("上传时间平均热度:\n%s", bucket_score.to_string())
    summary["csv"] = out_csv
    summary["chart"] = chart
    return summary


def main():
    parser = argparse.ArgumentParser(description="分析某个频道在热榜中的表现")
    parser.add_argument("--channel", required=True)
    parser.add_argument("--log-level", default=None)
    args = parser.parse_args()
    if args.log_level:
        logging.getLogger().setLevel(args.log_level.upper())
    result = analyze_channel(args.channel)
    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
