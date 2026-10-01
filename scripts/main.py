# scripts/main.py
import sys
import os
import time
import logging
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *
from scripts.scraper import YouTubeTrendingScraper
from scripts.analyzer import PopularityAnalyzer
from scripts.visualizer import PopularityVisualizer

import pandas as pd

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 60)
    logger.info(f"启动 {PROJECT_NAME} v{VERSION}")
    logger.info("=" * 60)
    
    # 第 1 步：爬取数据
    logger.info("\n【步骤 1】爬取 YouTube 热榜数据...")
    scraper = YouTubeTrendingScraper()
    videos = scraper.scrape_all_regions()
    
    if not videos:
        logger.error("爬��失败，程序退出")
        return
    
    # 保存原始数据
    output_file = os.path.join(RAW_DATA_DIR, f"raw_videos_{get_timestamp()}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
    logger.info(f"✓ 原始数据已保存: {output_file}")
    
    # 第 2 步：分析数据
    logger.info("\n【步骤 2】分析热度数据...")
    analyzer = PopularityAnalyzer()
    df_analyzed = analyzer.analyze(videos)
    
    # 保存分析结果
    analyzed_file = os.path.join(PROCESSED_DATA_DIR, f"analyzed_{get_timestamp()}.csv")
    df_analyzed.to_csv(analyzed_file, index=False, encoding='utf-8-sig')
    logger.info(f"✓ 分析结果已保存: {analyzed_file}")
    
    # 第 3 步：生成可视化
    logger.info("\n【步骤 3】生成可视化图表...")
    visualizer = PopularityVisualizer(df_analyzed)
    visualizer.generate_all()
    
    # 第 4 步：输出摘要
    logger.info("\n【步骤 4】数据摘要")
    logger.info("-" * 60)
    
    stats = analyzer.get_statistics(df_analyzed)
    logger.info(f"总视频数: {stats['total_videos']}")
    logger.info(f"涵盖地区: {stats['regions']}")
    logger.info(f"平均播放量: {stats['avg_views']:.0f}")
    logger.info(f"平均热度分数: {stats['avg_score']:.2f}")
    logger.info(f"最活跃频道: {stats['top_channel']}")
    
    logger.info("\n【TOP 10 热榜视频】")
    logger.info("-" * 60)
    top_10 = df_analyzed.head(10)[['rank', 'title', 'channel', 'views', 'popularity_score', 'region']]
    print(top_10.to_string(index=False))
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ 所有任务完成！")
    logger.info("=" * 60)
    logger.info(f"\n数据位置:")
    logger.info(f"  - 原始数据: {RAW_DATA_DIR}")
    logger.info(f"  - 分析结果: {PROCESSED_DATA_DIR}")
    logger.info(f"  - 可视化: {os.path.join(PROCESSED_DATA_DIR, 'visualizations')}")

if __name__ == "__main__":
    main()
