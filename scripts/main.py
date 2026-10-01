# scripts/main.py
import argparse
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    LOG_FORMAT,
    LOG_LEVEL,
    PROCESSED_DATA_DIR,
    PROJECT_NAME,
    RAW_DATA_DIR,
    VERSION,
    VISUALIZATIONS_DIR,
    get_timestamp,
)
from scripts.analyzer import PopularityAnalyzer, export_dataframe
from scripts.report import write_html_report
from scripts.scraper import YouTubeTrendingScraper, _parse_regions
from scripts.visualizer import PopularityVisualizer

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def run_pipeline(regions=None):
    logger.info("=" * 60)
    logger.info("启动 %s v%s", PROJECT_NAME, VERSION)
    logger.info("=" * 60)

    logger.info("\n【步骤 1】爬取 YouTube 热榜数据...")
    scraper = YouTubeTrendingScraper()
    videos = scraper.scrape_all_regions(regions)
    if not videos:
        logger.error("爬取失败，程序退出")
        return None

    raw_file = os.path.join(RAW_DATA_DIR, f"raw_videos_{get_timestamp()}.json")
    with open(raw_file, "w", encoding="utf-8") as handle:
        json.dump(videos, handle, ensure_ascii=False, indent=2)
    logger.info("✓ 原始数据已保存: %s", raw_file)

    logger.info("\n【步骤 2】分析热度数据...")
    analyzer = PopularityAnalyzer()
    df_analyzed = analyzer.analyze(videos)
    paths = export_dataframe(df_analyzed, f"analyzed_{get_timestamp()}")
    for kind, path in paths.items():
        logger.info("✓ 分析结果已保存 (%s): %s", kind, path)

    logger.info("\n【步骤 3】生成可视化图表...")
    visualizer = PopularityVisualizer(df_analyzed)
    visualizer.generate_all()

    logger.info("\n【步骤 4】数据摘要")
    logger.info("-" * 60)
    stats = analyzer.get_statistics(df_analyzed)
    logger.info("总视频数: %s", stats["total_videos"])
    logger.info("涵盖地区: %s", stats["regions"])
    logger.info("平均播放量: %.0f", stats["avg_views"])
    logger.info("平均热度分数: %.2f", stats["avg_score"])
    logger.info("最活跃频道: %s", stats["top_channel"])

    logger.info("\n【TOP 10 热榜视频】")
    logger.info("-" * 60)
    columns = [c for c in ["rank", "title", "channel", "views", "popularity_score", "region"] if c in df_analyzed.columns]
    print(df_analyzed[columns].head(10).to_string(index=False))

    report_path = write_html_report(df_analyzed, stats)
    logger.info("✓ HTML 报告已保存: %s", report_path)

    logger.info("\n" + "=" * 60)
    logger.info("✓ 所有任务完成！")
    logger.info("=" * 60)
    logger.info("\n数据位置:")
    logger.info("  - 原始数据: %s", RAW_DATA_DIR)
    logger.info("  - 分析结果: %s", PROCESSED_DATA_DIR)
    logger.info("  - 可视化: %s", VISUALIZATIONS_DIR)
    return {
        "raw": raw_file,
        "exports": paths,
        "report": report_path,
        "stats": stats,
        "dataframe": df_analyzed,
    }


def main():
    parser = argparse.ArgumentParser(description="一键抓取、分析并可视化 YouTube 热榜")
    parser.add_argument("--regions", help="逗号分隔的地区代码，例如 US,JP")
    parser.add_argument("--log-level", default=None)
    args = parser.parse_args()
    if args.log_level:
        logging.getLogger().setLevel(args.log_level.upper())
    result = run_pipeline(_parse_regions(args.regions))
    if result is None:
        sys.exit(1)
    return result


if __name__ == "__main__":
    main()
