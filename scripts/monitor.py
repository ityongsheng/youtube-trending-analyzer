# scripts/monitor.py
"""对比最近两次采集，打印新上榜视频与热度变化。"""
import argparse
import json
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOG_FORMAT, LOG_LEVEL, RAW_DATA_DIR
from scripts.main import run_pipeline
from scripts.scraper import _parse_regions

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def _load_raw_files():
    files = sorted(
        os.path.join(RAW_DATA_DIR, name)
        for name in os.listdir(RAW_DATA_DIR)
        if name.endswith(".json")
    )
    return files


def _ids(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {item.get("video_id"): item for item in data if item.get("video_id")}


def check_once():
    files = _load_raw_files()
    if not files:
        logger.warning("没有历史数据，无法对比。可加 --scrape 先采集。")
        return {"status": "empty"}
    latest = files[-1]
    latest_map = _ids(latest)
    logger.info("最新快照: %s（%s 条）", latest, len(latest_map))
    if len(files) == 1:
        logger.info("只有一份快照，已建立监控基线。")
        return {"status": "baseline", "latest": latest, "count": len(latest_map)}
    previous = files[-2]
    previous_map = _ids(previous)
    new_ids = [vid for vid in latest_map if vid not in previous_map]
    gone_ids = [vid for vid in previous_map if vid not in latest_map]
    logger.info("对比 %s -> %s", os.path.basename(previous), os.path.basename(latest))
    logger.info("新出现: %s，消失: %s", len(new_ids), len(gone_ids))
    for vid in new_ids[:10]:
        item = latest_map[vid]
        logger.info("  新上榜 [%s] %s (%s)", item.get("region"), item.get("title"), item.get("channel"))
    return {
        "status": "compared",
        "latest": latest,
        "previous": previous,
        "new": len(new_ids),
        "gone": len(gone_ids),
    }


def main():
    parser = argparse.ArgumentParser(description="监控热榜变化")
    parser.add_argument("--interval", type=int, default=3600, help="循环间隔秒数")
    parser.add_argument("--once", action="store_true", help="只检查一次")
    parser.add_argument("--scrape", action="store_true", help="检查前先跑一遍采集")
    parser.add_argument("--regions", default=None)
    parser.add_argument("--log-level", default=None)
    args = parser.parse_args()
    if args.log_level:
        logging.getLogger().setLevel(args.log_level.upper())
    regions = _parse_regions(args.regions)

    def cycle():
        if args.scrape:
            run_pipeline(regions)
        return check_once()

    if args.once:
        result = cycle()
        if result.get("status") == "empty" and not args.scrape:
            sys.exit(1)
        return
    logger.info("监控已启动，间隔 %s 秒", args.interval)
    while True:
        cycle()
        time.sleep(max(args.interval, 1))


if __name__ == "__main__":
    main()
