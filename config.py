# config.py
import os
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ===== 项目配置 =====
PROJECT_NAME = "YouTube Trending Analyzer"
VERSION = "1.0.0"

# ===== 数据路径 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
VISUALIZATIONS_DIR = os.path.join(PROCESSED_DATA_DIR, "visualizations")

os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(VISUALIZATIONS_DIR, exist_ok=True)

# ===== 爬虫配置 =====
# 支持的国家代码和语言
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

# 请求头
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

# 请求延迟（秒）- 避免被限流
REQUEST_DELAY = 2

# 代理池（可在 .env 或运行时注入）
PROXIES = [p.strip() for p in os.getenv("PROXIES", "").split(",") if p.strip()]

# 是否启用代理轮换
USE_PROXY_ROTATION = os.getenv("USE_PROXY_ROTATION", "false").lower() in {"1", "true", "yes"}

# 请求超时与重试
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))

# 每个地区最多获取视频数
MAX_VIDEOS_PER_REGION = int(os.getenv("MAX_VIDEOS_PER_REGION", "20"))

# 并发补充点赞/评论时的线程数
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "6"))

# 可选：YouTube Data API v3。未设置时走网页/Innertube，不需要密钥。
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
USE_OFFICIAL_API = os.getenv("USE_OFFICIAL_API", "false").lower() in {"1", "true", "yes"}

# 可选代理服务
PROXY_API_URL = os.getenv("PROXY_API_URL", "")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "")

# ===== 热度计算配置 =====
# 热度分数 = (views * views_weight + comments * comments_weight + likes * likes_weight) / (hours ^ time_decay)
POPULARITY_WEIGHTS = {
    "views": 1.0,           # 播放量权重
    "comments": 0.5,        # 评论数权重
    "likes": 0.3,           # 点赞数权重
    "time_decay": 0.5,      # 时间衰减指数（越小衰减越慢）
}

# ===== 输出配置 =====
EXPORT_FORMATS = ["csv", "json", "xlsx"]
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 本周播放量排序的搜索过滤参数（YouTube 已于 2025-07 移除综合 Trending 页）
SEARCH_VIEW_FILTER = "CAMSBAgDEAE="

# ===== 日志配置 =====
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")
