# scripts/scheduler.py
"""定时采集。默认每天 08:00 运行完整流水线。"""
import argparse
import logging
import os
import sys
import time

import schedule

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOG_FORMAT, LOG_LEVEL
from scripts.main import run_pipeline
from scripts.scraper import _parse_regions

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def job(regions=None):
    logger.info("定时任务开始")
    result = run_pipeline(regions)
    logger.info("定时任务结束: %s", "成功" if result else "失败")
    return result


def start(once=False, regions=None, daily_at="08:00"):
    if once:
        return job(regions)
    schedule.every().day.at(daily_at).do(job, regions=regions)
    # 也演示 README 里的其他写法不会同时启用，避免重复跑。
    logger.info("已注册每天 %s 的采集任务。按 Ctrl+C 结束。", daily_at)
    logger.info("下一运行时间: %s", schedule.next_run())
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="定时抓取并分析 YouTube 热榜")
    parser.add_argument("--once", action="store_true", help="立即运行一次后退出")
    parser.add_argument("--at", default="08:00", help="每天运行时间 HH:MM")
    parser.add_argument("--regions", default=None)
    parser.add_argument("--log-level", default=None)
    args = parser.parse_args()
    if args.log_level:
        logging.getLogger().setLevel(args.log_level.upper())
    start(once=args.once, regions=_parse_regions(args.regions), daily_at=args.at)


if __name__ == "__main__":
    main()
