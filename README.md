# YouTube Trending Analyzer 🎬

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个功能完整的 **YouTube 热度分析工具**，支持多国热榜抓取、热度评分、数据分析和可视化。

**核心功能：**
- 🌍 多国家/地区 YouTube 热榜采集
- 📊 智能热度评分算法（综合浏览量、评论、点赞、时间因素）
- 🔄 代理池轮换 + 延迟控制（反爬虫）
- ⏰ 定时自动采集（支持每天/每周/自定义）
- 📈 可视化数据展示（4 种图表）
- 📥 多格式导出（CSV / JSON / XLSX）

---

## 📋 目录

- [快速开始](#快速开始)
- [详细安装](#详细安装)
- [使用方法](#使用方法)
- [热度评分公式](#热度评分公式)
- [配置说明](#配置说明)
- [高级功能](#高级功能)
- [常见问题](#常见问题)
- [项目结构](#项目结构)

---


> **数据来源（2026）：** YouTube 已于 2025-07 下线综合 Trending 页（`FEtrending` 返回 400）。
> 爬虫仍会先尝试该页面和 Innertube browse；失败后按地区抓取「本周 + 播放量排序」的公开搜索结果，
> 再用 player / watch-next 补全播放量、点赞和评论。官方 Data API 只有在设置了 `YOUTUBE_API_KEY`
> 且 `USE_OFFICIAL_API=true` 时才会使用。

## 🚀 快速开始

### 最快 3 分钟上手

```bash
# 1. 克隆项目
git clone https://github.com/ityongsheng/youtube-trending-analyzer.git
cd youtube-trending-analyzer

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 一键运行（抓取 + 分析 + 可视化）
python scripts/main.py
```

**结果输出路径：**
```
data/
├── raw/               # 原始爬虫数据 (JSON)
├── processed/         # 分析后的数据 (CSV)
└── visualizations/    # 图表输出 (PNG)
```

---

## 📦 详细安装

### 系统要求

- Python 3.9 或更高版本（已在 3.13 验证）
- pip 包管理器
- 100 MB 硬盘空间
- 网络连接

### 步骤 1：克隆仓库

```bash
git clone https://github.com/ityongsheng/youtube-trending-analyzer.git
cd youtube-trending-analyzer
```

### 步骤 2：创建虚拟环境

**推荐**使用虚拟环境隔离依赖：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux / macOS
source venv/bin/activate

# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
```

### 步骤 3：安装依赖包

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**依赖说明：**

| 包名 | 版本 | 用途 |
|------|------|------|
| requests | 2.32.3 | HTTP 请求 |
| beautifulsoup4 | 4.12.3 | HTML 解析 |
| pandas | 2.2.3 | 数据处理 |
| matplotlib | 3.9.4 | 图表绘制 |
| seaborn | 0.13.2 | 高级绘图 |
| schedule | 1.2.2 | 定时任务 |

### 步骤 4：验证安装

```bash
python -c "import requests, pandas, matplotlib; print('✓ 安装成功')"
```

---

## 💡 使用方法

### 方式 1：一键运行所有流程

最推荐，自动执行：爬取 → 分析 → 可视化

```bash
python scripts/main.py
```

**输出示例：**
```
============================================================
启动 YouTube Trending Analyzer v1.0.0
============================================================

【步骤 1】爬取 YouTube 热榜数据...
开始爬取 US 地区热榜...
✓ 原始数据已保存: data/raw/raw_videos_20240115_143022.json

【步骤 2】分析热度数据...
✓ 分析结果已保存: data/processed/analyzed_20240115_143022.csv

【步骤 3】生成可视化图表...
✓ 已保存: top_10_videos.png
✓ 已保存: by_region.png
✓ 已保存: views_vs_score.png
✓ 已保存: top_channels.png

【步骤 4】数据摘要
------------------------------------------------------------
总视频数: 500
涵盖地区: 10
平均播放量: 1,234,567
平均热度分数: 8542.34
最活跃频道: YouTube

【TOP 10 热榜视频】
------------------------------------------------------------
rank  title                          channel    views  popularity_score  region
   1  Amazing Video Title            ChannelA   5M     45823.12          US
   2  Trending Content               ChannelB   3M     38291.45          JP
   ...
```

### 方式 2：分步执行

#### 只爬取数据

```bash
python scripts/scraper.py
```

输出：`data/raw/raw_videos_YYYYMMDD_HHMMSS.json`

#### 只分析数据（前提：已有原始数据）

```bash
python scripts/analyzer.py
```

输出：`data/processed/analyzed_YYYYMMDD_HHMMSS.csv`

#### 只生成图表（前提：已有分析结果）

```bash
python scripts/visualizer.py
```

输出：`data/processed/visualizations/` 目录下的 PNG 文件

### 方式 3：定时自动采集

每天早上 8 点自动运行爬虫和分析：

```bash
python scripts/scheduler.py
```

**定制采集时间：** 编辑 `scripts/scheduler.py`

```python
# 每天早上 8 点
schedule.every().day.at("08:00").do(job)

# 每 6 小时运行一次
schedule.every(6).hours.do(job)

# 每周一 10 点
schedule.every().monday.at("10:00").do(job)
```

---

## 📊 热度评分公式

### 核心算法

热度分数 = **基础分数** / **时间衰减因子**

```
基础分数 = views × 1.0 + comments × 0.5 + likes × 0.3
时间衰减 = (发布时间差/小时) ^ 0.5
热度分数 = 基础分数 / 时间衰减
```

### 参数解释

| 参数 | 默认值 | 说明 |
|------|--------|------|
| **views_weight** | 1.0 | 浏览量权重（影响最大） |
| **comments_weight** | 0.5 | 评论数权重（表示参与度） |
| **likes_weight** | 0.3 | 点赞数权重（表示认可度） |
| **time_decay** | 0.5 | 时间衰减指数（值越小衰减越慢） |

### 示例计算

**视频 A：**
- 浏览量：1,000,000
- 评论数：5,000
- 点赞数：20,000
- 发布时间：2 小时前

```
基础分数 = 1000000 × 1.0 + 5000 × 0.5 + 20000 × 0.3
        = 1000000 + 2500 + 6000
        = 1,008,500

热度分数 = 1,008,500 / (2 ^ 0.5)
        = 1,008,500 / 1.414
        ≈ 713,155
```

### 自定义公式

编辑 `config.py` 中的 `POPULARITY_WEIGHTS`：

```python
POPULARITY_WEIGHTS = {
    "views": 1.0,        # 增大此值使浏览量更重要
    "comments": 0.5,     # 增大此值使评论数更重要
    "likes": 0.3,        # 增大此值使点赞数更重要
    "time_decay": 0.5,   # 增大此值使新视频更有优势
}
```

---

## ⚙️ 配置说明

### 主配置文件：`config.py`

#### 1. 国家/地区配置

```python
COUNTRIES = {
    "US": "en",      # 美国
    "JP": "ja",      # 日本
    "IN": "hi",      # 印度
    "BR": "pt",      # 巴西
    "GB": "en",      # 英国
    "DE": "de",      # 德国
    "FR": "fr",      # 法国
    "CN": "zh-Hans", # 中国
    "KR": "ko",      # 韩国
    "MX": "es",      # 墨西哥
}
```

**添加更多国家：** 添加新键值对

```python
COUNTRIES = {
    # ... 现有国家
    "IT": "it",      # 意大利
    "ES": "es",      # 西班牙
    "RU": "ru",      # 俄罗斯
}
```

#### 2. 代理配置（反爬虫）

```python
# 添加你的代理池
PROXIES = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
    "socks5://proxy3.example.com:1080",
]

# 是否启用代理轮换
USE_PROXY_ROTATION = True

# 请求延迟（秒）- 避免被限流
REQUEST_DELAY = 2  # 建议 2-5 秒
```

#### 3. 请求超时配置

```python
REQUEST_TIMEOUT = 10  # 单个请求超时时间（秒）
MAX_RETRIES = 3       # 失败重试次数
RETRY_DELAY = 5       # 重试间隔（秒）
```

#### 4. 数据导出配置

```python
EXPORT_FORMATS = ["csv", "json", "xlsx"]  # 支持的导出格式
MAX_VIDEOS_PER_REGION = 50  # 每个地区最多获取视频数
```

### 运行时环境变量

创建 `.env` 文件（可选）：

```bash
# 代理池地址（若使用代理服务）
PROXY_API_URL=https://api.example.com/proxy
PROXY_API_KEY=your_api_key

# 日志级别（DEBUG/INFO/WARNING/ERROR）
LOG_LEVEL=INFO

# 性能参数
NUM_WORKERS=4
BATCH_SIZE=10
```

---

## 🔧 高级功能

### 1. 更稳定的页面解析

脚本内置了多种解析策略：

```python
# scraper.py 中已包含：
# - ytInitialData JSON 提取
# - gridVideoRenderer 解析
# - 多版本选择器支持
# - 自动回退机制

# 如果页面结构改变，脚本会自动尝试备选方案
```

**手动更新解析器：**

编辑 `scripts/scraper.py` 中的 `_extract_videos()` 方法

```python
def _extract_videos(self, html_text, region):
    # 第一尝试：ytInitialData
    videos = self._extract_from_yt_initial_data(html_text)
    
    # 失败回退：Selenium 动态渲染
    if not videos:
        videos = self._extract_with_selenium(html_text)
    
    # 最后回退：BeautifulSoup 直接解析
    if not videos:
        videos = self._extract_with_beautifulsoup(html_text)
    
    return videos
```

### 2. 代理池 + 延迟控制

```python
# 在 scraper.py 中启用代理轮换
scraper = YouTubeTrendingScraper(use_proxy=True)
scraper.proxy_list = [
    "http://proxy1:8080",
    "http://proxy2:8080",
    "socks5://proxy3:1080",
]

# 自动在每个请求间增加随机延迟（1-5 秒）
scraper.use_random_delay = True
scraper.delay_range = (1, 5)
```

**使用代理 API 服务（推荐）：**

```python
# 申请免费代理（如 free-proxy-list.net）
# 或付费服务（如 brightdata.com, scrapingbee.com）

# 配置代理轮换
from scripts.scraper import YouTubeTrendingScraper

scraper = YouTubeTrendingScraper()
scraper.set_proxy_rotation(enabled=True, api_url="your_api_url")
```

### 3. 定时采集 + 历史对比

```bash
# 启动定时任务
python scripts/scheduler.py
```

**输出：** 每次采集的数据会保存为独立文件

```
data/processed/
├── analyzed_20240115_080000.csv
├── analyzed_20240116_080000.csv  # 第二天采集
├── analyzed_20240117_080000.csv  # 第三天采集
└── trend_analysis.csv            # 自动生成的趋势报告
```

**生成趋势报告：**

```python
from scripts.trend_analyzer import TrendAnalyzer

analyzer = TrendAnalyzer(data_dir="data/processed")
trend_report = analyzer.generate_trend_report()
# 输出：热度趋势、新视频出现频率、频道排名变化
```

### 4. 完整版热度分析器功能

#### 功能 1：实时热度监控

```bash
python scripts/monitor.py --interval 3600  # 每小时检查一次
```

#### 功能 2：热度预测

```python
from scripts.predictors import PopularityPredictor

predictor = PopularityPredictor()
future_score = predictor.predict_48h_later(video_id="abc123")
# 输出：预测该视频 48 小时后的热度
```

#### 功能 3：频道深度分析

```bash
python scripts/channel_analyzer.py --channel "ChannelName"
```

输出：
- 频道视频热度分布
- 上传规律分析
- 最佳发布时间
- 内容类型偏好

#### 功能 4：竞品分析

```bash
python scripts/competitor_analysis.py \
  --channels "Channel1,Channel2,Channel3" \
  --metrics "views,engagement_rate,upload_frequency"
```

---

## 🐛 常见问题

### Q1: 脚本运行出错 "No module named xxx"

**答：** 依赖未安装。运行：

```bash
pip install -r requirements.txt -U
```

### Q2: 爬虫被限流（返回 403）

**答：** YouTube 检测到异常请求。解决方案：

1. **增加延迟：**
```python
# config.py
REQUEST_DELAY = 5  # 改为 5-10 秒
```

2. **使用代理：**
```python
scraper = YouTubeTrendingScraper(use_proxy=True)
```

3. **减少采集频率：**
```bash
# 改为每天只采集一次
schedule.every().day.at("23:00").do(job)
```

### Q3: 数据为空或数据不完整

**答：** YouTube 页面结构可能已变化。检查：

```bash
# 1. 测试网络连接
ping youtube.com

# 2. 查看详细日志
python scripts/scraper.py --log-level DEBUG

# 3. 检查 HTML 源码是否改变
python -c "
import requests
from config import USER_AGENTS
import random
headers = {'User-Agent': random.choice(USER_AGENTS)}
r = requests.get('https://www.youtube.com/feed/trending', headers=headers)
print('状态码:', r.status_code)
print('页面长度:', len(r.text))
"
```

### Q4: 中文显示乱码

**答：** 字体配置问题。解决：

```python
# 在 visualizer.py 最上面添加
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False
```

### Q5: 如何只采集某个国家的数据？

**答：** 修改 `config.py`：

```python
# 只保留想要的国家
COUNTRIES = {
    "US": "en",
    "JP": "ja",
}
```

或在命令行指定：

```bash
python scripts/scraper.py --regions US,JP,IN
```

### Q6: 能否集成 YouTube API？

**答：** 可以。需要：

1. 在 [Google Cloud Console](https://console.cloud.google.com/) 创建项目
2. 启用 YouTube Data API v3
3. 生成 API Key
4. 在 `config.py` 中配置：

```python
YOUTUBE_API_KEY = "your_api_key_here"
USE_OFFICIAL_API = True  # 启用官方 API
```

---

## 📁 项目结构

```
youtube-trending-analyzer/
│
├── README.md                    # 项目说明文档
├── config.py                    # 全局配置文件
├── requirements.txt             # 依赖列表
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git 忽略规则
│
├── scripts/                     # Python 脚本目录
│   ├── __init__.py
│   ���── main.py                  # 主程序（一键运行）
│   ├── scraper.py               # YouTube 爬虫
│   ├── analyzer.py              # 热度分析器
│   ├── visualizer.py            # 图表生成器
│   ├── scheduler.py             # 定时任务
│   ├── monitor.py               # 实时监控（可选）
│   ├── trend_analyzer.py        # 趋势分析（可选）
│   ├── channel_analyzer.py      # 频道分析（可选）
│   └── competitor_analysis.py   # 竞品分析（可选）
│
├── data/                        # 数据目录
│   ├── raw/                     # 原始爬虫数据 (JSON)
│   │   └── raw_videos_*.json
│   └── processed/               # 处理后数据
│       ├── analyzed_*.csv
│       ├── analyzed_*.xlsx
│       ├── trend_report_*.csv
│       └── visualizations/      # 图表输出 (PNG)
│           ├── top_10_videos.png
│           ├── by_region.png
│           ├── views_vs_score.png
│           └── top_channels.png
│
├── docs/                        # 文档目录
│   ├── INSTALL.md              # 安装指南
│   ├── API_GUIDE.md            # API 集成指南
│   ├── TROUBLESHOOTING.md      # 故障排除
│   └── EXAMPLES.md             # 使用示例
│
└── tests/                       # 测试目录（可选）
    ├── test_scraper.py
    ├── test_analyzer.py
    └── test_visualizer.py
```

---

## 🎯 功能完整性检查表

### 核心功能

- [x] 多国热榜采集
- [x] 热度评分算法
- [x] 数据分析与排序
- [x] 图表可视化
- [x] CSV/JSON 导出

### 反爬虫功能

- [x] User-Agent 随机化
- [x] 请求延迟控制
- [x] 代理池支持
- [x] 失败重试机制
- [x] 请求头伪装

### 定时采集

- [x] 每天定时运行
- [x] 自定义时间表
- [x] 后台持续监控
- [x] 历史数据对比

### 完整分析功能

- [x] 热度趋势分析
- [x] 频道排名统计
- [x] 内容类型分析
- [x] 地区对比分析
- [x] 竞品对标分析

### 数据输出

- [x] CSV 导出
- [x] JSON 导出
- [x] XLSX 导出
- [x] PNG 图表
- [x] HTML 报告（计划中）

---

## 📈 使用案例

### 案例 1：内容创作者

监控热榜视频特征，优化自己的内容策略：

```bash
python scripts/main.py
# 查看 top_channels.png 了解哪些频道最活跃
# 查看 analyzed_*.csv 找出高热度视频的共同特点
```

### 案例 2：数据分析师

定时采集数据，生成趋势报告：

```bash
# 每天 8 点自动采集
python scripts/scheduler.py

# 一周后查看 trend_report_*.csv
```

### 案例 3：营销人员

跟踪竞品热度变化：

```bash
python scripts/competitor_analysis.py \
  --channels "Competitor1,Competitor2" \
  --output competitor_report.csv
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 报告 Bug

```bash
# 提供：
# 1. Python 版本
# 2. 操作系统
# 3. 完整错误信息
# 4. 复现步骤
```

### 提交改进

```bash
git clone https://github.com/ityongsheng/youtube-trending-analyzer.git
git checkout -b feature/your-feature
# 做改动
git commit -m "Add: your feature description"
git push origin feature/your-feature
# 提交 Pull Request
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 💬 支持

- 📧 邮件：github@example.com
- 💬 提 Issue：https://github.com/ityongsheng/youtube-trending-analyzer/issues
- 📚 文档：https://github.com/ityongsheng/youtube-trending-analyzer/wiki

---

## 🙏 致谢

- YouTube 数据来源
- 开源社区的支持

---

**⭐ 如果项目对你有帮助，请 Star 一下！**

---

**最后更新：2024-01-15**
