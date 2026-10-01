# scripts/visualizer.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import logging
import sys
import os
from pathlib import Path

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class PopularityVisualizer:
    def __init__(self, df):
        self.df = df
        self.output_dir = os.path.join(PROCESSED_DATA_DIR, 'visualizations')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def plot_top_10_videos(self):
        """绘制热度前 10 的视频"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        top_10 = self.df.head(10)
        
        ax.barh(range(len(top_10)), top_10['popularity_score'].values)
        ax.set_yticks(range(len(top_10)))
        ax.set_yticklabels([f"{i+1}. {title[:30]}..." for i, title in enumerate(top_10['title'].values)])
        ax.set_xlabel('热度分数')
        ax.set_title('YouTube 热度前 10 视频')
        ax.invert_yaxis()
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'top_10_videos.png'), dpi=100, bbox_inches='tight')
        logger.info("已保存: top_10_videos.png")
        plt.close()
    
    def plot_by_region(self):
        """按地区分析热度"""
        if len(self.df) == 0:
            logger.warning("数据为空，跳过地区分析")
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        region_stats = self.df.groupby('region')['popularity_score'].mean().sort_values(ascending=False)
        
        region_stats.plot(kind='bar', ax=ax, color='skyblue')
        ax.set_title('各地区平均热度分数')
        ax.set_xlabel('地区')
        ax.set_ylabel('平均热度分数')
        ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'by_region.png'), dpi=100, bbox_inches='tight')
        logger.info("已保存: by_region.png")
        plt.close()
    
    def plot_views_vs_score(self):
        """播放量 vs 热度分数"""
        if len(self.df) == 0:
            logger.warning("数据为空，跳过散点图分析")
            return
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        scatter = ax.scatter(self.df['views'], self.df['popularity_score'], 
                           c=self.df['region'].astype('category').cat.codes, 
                           s=100, alpha=0.6, cmap='viridis')
        
        ax.set_xlabel('播放量')
        ax.set_ylabel('热度分数')
        ax.set_title('播放量 vs 热度分数')
        ax.set_xscale('log')
        ax.set_yscale('log')
        
        plt.colorbar(scatter, label='地区')
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'views_vs_score.png'), dpi=100, bbox_inches='tight')
        logger.info("已保存: views_vs_score.png")
        plt.close()
    
    def plot_channel_distribution(self):
        """频道分布"""
        if len(self.df) == 0:
            logger.warning("数据为空，跳过频道分析")
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        top_channels = self.df['channel'].value_counts().head(10)
        
        top_channels.plot(kind='barh', ax=ax, color='coral')
        ax.set_title('热榜视频频道 Top 10')
        ax.set_xlabel('视频数量')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'top_channels.png'), dpi=100, bbox_inches='tight')
        logger.info("已保存: top_channels.png")
        plt.close()
    
    def generate_all(self):
        """生成所有图表"""
        logger.info("开始生成可视化图表...")
        
        self.plot_top_10_videos()
        self.plot_by_region()
        self.plot_views_vs_score()
        self.plot_channel_distribution()
        
        logger.info(f"所有图表已保存到 {self.output_dir}")

def main():
    # 读取最新的分析结果
    csv_files = sorted([f for f in os.listdir(PROCESSED_DATA_DIR) if f.endswith('.csv') and f.startswith('analyzed_')])
    
    if not csv_files:
        logger.error("未找到分析结果文件，请先运行 analyzer.py")
        return
    
    latest_csv = os.path.join(PROCESSED_DATA_DIR, csv_files[-1])
    logger.info(f"读取分析结果: {latest_csv}")
    
    df = pd.read_csv(latest_csv)
    
    # 生成可视化
    visualizer = PopularityVisualizer(df)
    visualizer.generate_all()

if __name__ == "__main__":
    main()
