# scripts/visualizer.py
import logging
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOG_FORMAT, LOG_LEVEL, PROCESSED_DATA_DIR, VISUALIZATIONS_DIR

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def configure_matplotlib_fonts():
    from matplotlib import font_manager
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                font_manager.fontManager.addfont(path)
                name = font_manager.FontProperties(fname=path).get_name()
                plt.rcParams["font.family"] = name
                plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
                break
            except Exception:
                continue
    else:
        plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

configure_matplotlib_fonts()
sns.set_theme(style="whitegrid")
configure_matplotlib_fonts()


class PopularityVisualizer:
    def __init__(self, df):
        self.df = df if df is not None else pd.DataFrame()
        self.output_dir = VISUALIZATIONS_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def _save(self, fig, name):
        path = os.path.join(self.output_dir, name)
        fig.tight_layout()
        fig.savefig(path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        logger.info("已保存: %s", name)
        return path

    def plot_top_10_videos(self):
        if len(self.df) == 0:
            logger.warning("数据为空，跳过 TOP10 图")
            return None
        fig, ax = plt.subplots(figsize=(12, 8))
        top_10 = self.df.head(10).iloc[::-1]
        labels = []
        for title in top_10["title"].astype(str):
            short = title if len(title) <= 32 else title[:32] + "..."
            labels.append(short)
        sns.barplot(
            x=top_10["popularity_score"].astype(float),
            y=labels,
            ax=ax,
            color="#4C78A8",
            orient="h",
        )
        ax.set_xlabel("热度分数")
        ax.set_ylabel("")
        ax.set_title("YouTube 热度前 10 视频")
        return self._save(fig, "top_10_videos.png")

    def plot_by_region(self):
        if len(self.df) == 0 or "region" not in self.df.columns:
            logger.warning("数据为空，跳过地区分析")
            return None
        fig, ax = plt.subplots(figsize=(12, 6))
        region_stats = (
            self.df.groupby("region")["popularity_score"].mean().sort_values(ascending=False)
        )
        sns.barplot(x=region_stats.index.astype(str), y=region_stats.values, ax=ax, color="#72B7B2")
        ax.set_title("各地区平均热度分数")
        ax.set_xlabel("地区")
        ax.set_ylabel("平均热度分数")
        ax.tick_params(axis="x", rotation=45)
        return self._save(fig, "by_region.png")

    def plot_views_vs_score(self):
        if len(self.df) == 0:
            logger.warning("数据为空，跳过散点图分析")
            return None
        fig, ax = plt.subplots(figsize=(12, 8))
        plot_df = self.df.copy()
        plot_df["views_plot"] = plot_df["views"].clip(lower=1)
        plot_df["score_plot"] = plot_df["popularity_score"].clip(lower=1)
        regions = plot_df["region"].astype(str)
        sns.scatterplot(
            data=plot_df,
            x="views_plot",
            y="score_plot",
            hue=regions,
            ax=ax,
            s=80,
            alpha=0.75,
        )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("播放量")
        ax.set_ylabel("热度分数")
        ax.set_title("播放量 vs 热度分数")
        ax.legend(title="地区", bbox_to_anchor=(1.02, 1), loc="upper left")
        return self._save(fig, "views_vs_score.png")

    def plot_channel_distribution(self):
        if len(self.df) == 0 or "channel" not in self.df.columns:
            logger.warning("数据为空，跳过频道分析")
            return None
        fig, ax = plt.subplots(figsize=(12, 6))
        channels = self.df["channel"].fillna("").astype(str)
        channels = channels[channels.str.len() > 0]
        if channels.empty:
            logger.warning("没有频道名，跳过频道分析")
            plt.close(fig)
            return None
        top_channels = channels.value_counts().head(10).sort_values(ascending=True)
        sns.barplot(x=top_channels.values, y=top_channels.index.astype(str), ax=ax, color="#E45756", orient="h")
        ax.set_title("热榜视频频道 Top 10")
        ax.set_xlabel("视频数量")
        ax.set_ylabel("")
        return self._save(fig, "top_channels.png")

    def generate_all(self):
        logger.info("开始生成可视化图表...")
        paths = {
            "top_10_videos": self.plot_top_10_videos(),
            "by_region": self.plot_by_region(),
            "views_vs_score": self.plot_views_vs_score(),
            "top_channels": self.plot_channel_distribution(),
        }
        logger.info("所有图表已保存到 %s", self.output_dir)
        return paths


def main():
    csv_files = sorted(
        f for f in os.listdir(PROCESSED_DATA_DIR)
        if f.endswith(".csv") and f.startswith("analyzed_")
    )
    if not csv_files:
        logger.error("未找到分析结果文件，请先运行 analyzer.py")
        return
    latest_csv = os.path.join(PROCESSED_DATA_DIR, csv_files[-1])
    logger.info("读取分析结果: %s", latest_csv)
    df = pd.read_csv(latest_csv)
    visualizer = PopularityVisualizer(df)
    visualizer.generate_all()


if __name__ == "__main__":
    main()
