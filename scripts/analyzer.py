# scripts/analyzer.py
import pandas as pd
import json
import logging
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class PopularityAnalyzer:
    def __init__(self):
        self.weights = POPULARITY_WEIGHTS
    
    def calculate_popularity_score(self, video):
        """
        计算热度分数
        
        公式: (views * comments_factor * likes_factor) / (hours_since_upload ^ decay)
        """
        try:
            views = video.get('views', 0) or 0
            comments = video.get('comments', 0) or 0
            likes = video.get('likes', 0) or 0
            
            # 计算发布时间差（小时）
            try:
                publish_time_str = video.get('publish_time', '')
                
                # 尝试解析发布时间
                if '小时前' in publish_time_str or 'hour' in publish_time_str.lower():
                    hours = int(''.join(filter(str.isdigit, publish_time_str.split()[0])))
                elif '天前' in publish_time_str or 'day' in publish_time_str.lower():
                    hours = int(''.join(filter(str.isdigit, publish_time_str.split()[0]))) * 24
                elif '分钟前' in publish_time_str or 'minute' in publish_time_str.lower():
                    hours = int(''.join(filter(str.isdigit, publish_time_str.split()[0]))) / 60
                else:
                    hours = 1  # 默认 1 小时
            except:
                hours = 1
            
            # 避免除以 0
            hours = max(hours, 0.5)
            
            # 热度分数计算
            base_score = (
                views * self.weights['views'] +
                comments * self.weights['comments'] +
                likes * self.weights['likes']
            )
            
            # 时间衰减
            popularity_score = base_score / (hours ** self.weights['time_decay'])
            
            return popularity_score
        
        except Exception as e:
            logger.debug(f"计算热度分数失败: {str(e)}")
            return 0
    
    def analyze(self, videos_list):
        """
        分析视频列表并计算热度分数
        
        Args:
            videos_list: 视频字典列表
            
        Returns:
            pd.DataFrame: 分析结果
        """
        logger.info(f"开始分析 {len(videos_list)} 个视频...")
        
        # 转换为 DataFrame
        df = pd.DataFrame(videos_list)
        
        # 计算热度分数
        df['popularity_score'] = df.apply(self.calculate_popularity_score, axis=1)
        
        # 按热度排序
        df = df.sort_values('popularity_score', ascending=False)
        
        # 添加排名
        df['rank'] = range(1, len(df) + 1)
        
        # 重新排列列
        columns_order = [
            'rank', 'title', 'channel', 'region', 'views', 'comments', 'likes',
            'publish_time', 'popularity_score', 'url', 'video_id', 'scraped_at'
        ]
        
        # 只保留存在的列
        existing_columns = [col for col in columns_order if col in df.columns]
        df = df[existing_columns]
        
        logger.info(f"分析完成，共 {len(df)} 个视频")
        return df
    
    def get_top_videos(self, df, n=10):
        """获取热度最高的 n 个视频"""
        return df.head(n)
    
    def get_by_region(self, df, region):
        """按地区筛选"""
        return df[df['region'] == region].head(10)
    
    def get_statistics(self, df):
        """获取统计信息"""
        stats = {
            'total_videos': len(df),
            'regions': df['region'].nunique() if len(df) > 0 else 0,
            'avg_views': df['views'].mean() if len(df) > 0 else 0,
            'avg_score': df['popularity_score'].mean() if len(df) > 0 else 0,
            'top_channel': df['channel'].value_counts().index[0] if len(df) > 0 else 'N/A',
        }
        return stats

def main():
    # 读取原始数据
    raw_files = sorted([f for f in os.listdir(RAW_DATA_DIR) if f.endswith('.json')])
    
    if not raw_files:
        logger.error("未找到原始数据文件，请先运行 scraper.py")
        return None
    
    latest_raw_file = os.path.join(RAW_DATA_DIR, raw_files[-1])
    logger.info(f"读取数据文件: {latest_raw_file}")
    
    with open(latest_raw_file, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    # 分析
    analyzer = PopularityAnalyzer()
    df_analyzed = analyzer.analyze(videos)
    
    # 保存分析结果
    output_file = os.path.join(PROCESSED_DATA_DIR, f"analyzed_{get_timestamp()}.csv")
    df_analyzed.to_csv(output_file, index=False, encoding='utf-8-sig')
    logger.info(f"分析结果已保存到 {output_file}")
    
    # 打印统计信息
    stats = analyzer.get_statistics(df_analyzed)
    logger.info(f"统计信息: {stats}")
    
    # 打印前 10
    logger.info("\n=== TOP 10 热榜视频 ===")
    print(df_analyzed[['rank', 'title', 'channel', 'views', 'popularity_score', 'region']].head(10).to_string(index=False))
    
    return df_analyzed

if __name__ == "__main__":
    main()
