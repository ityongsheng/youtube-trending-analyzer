# scripts/report.py
"""HTML report for a scored dataframe."""
import html
import os
from datetime import datetime

from config import PROCESSED_DATA_DIR, PROJECT_NAME, VERSION, VISUALIZATIONS_DIR, get_timestamp


def write_html_report(df, stats):
    stamp = get_timestamp()
    path = os.path.join(PROCESSED_DATA_DIR, f"report_{stamp}.html")
    rows = []
    show = df.head(20)
    for _, row in show.iterrows():
        title = html.escape(str(row.get("title", "")))
        url = html.escape(str(row.get("url", "")), quote=True)
        rows.append(
            "<tr>"
            f"<td>{int(row.get('rank', 0))}</td>"
            f"<td><a href=\"{url}\">{title}</a></td>"
            f"<td>{html.escape(str(row.get('channel', '')))}</td>"
            f"<td>{html.escape(str(row.get('region', '')))}</td>"
            f"<td>{int(row.get('views', 0) or 0):,}</td>"
            f"<td>{int(row.get('likes', 0) or 0):,}</td>"
            f"<td>{int(row.get('comments', 0) or 0):,}</td>"
            f"<td>{float(row.get('popularity_score', 0) or 0):,.1f}</td>"
            "</tr>"
        )
    images = []
    for name in ("top_10_videos.png", "by_region.png", "views_vs_score.png", "top_channels.png"):
        image_path = os.path.join(VISUALIZATIONS_DIR, name)
        if os.path.exists(image_path):
            rel = os.path.relpath(image_path, PROCESSED_DATA_DIR)
            images.append(f'<figure><img src="{html.escape(rel)}" alt="{name}"><figcaption>{name}</figcaption></figure>')
    document = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{html.escape(PROJECT_NAME)} 报告</title>
<style>
body {{ font-family: "Noto Serif CJK SC", sans-serif; margin: 24px; color: #222; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 6px 8px; font-size: 14px; }}
th {{ background: #f4f6f8; }}
img {{ max-width: 720px; height: auto; }}
.stats {{ display: flex; gap: 16px; flex-wrap: wrap; }}
.stats div {{ background: #f7f7f7; padding: 12px 16px; border-radius: 8px; }}
</style>
</head>
<body>
<h1>{html.escape(PROJECT_NAME)} v{html.escape(VERSION)}</h1>
<p>生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
<div class="stats">
  <div>总视频数<br><strong>{stats.get("total_videos", 0)}</strong></div>
  <div>涵盖地区<br><strong>{stats.get("regions", 0)}</strong></div>
  <div>平均播放量<br><strong>{stats.get("avg_views", 0):,.0f}</strong></div>
  <div>平均热度分数<br><strong>{stats.get("avg_score", 0):,.2f}</strong></div>
  <div>最活跃频道<br><strong>{html.escape(str(stats.get("top_channel", "N/A")))}</strong></div>
</div>
<h2>TOP 20</h2>
<table>
<thead><tr><th>排名</th><th>标题</th><th>频道</th><th>地区</th><th>播放量</th><th>点赞</th><th>评论</th><th>热度分数</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
<h2>图表</h2>
{''.join(images) if images else '<p>暂无图表</p>'}
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(document)
    return path
