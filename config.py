# config.py
import os
from datetime import datetime

# ===== 项目配置 =====
PROJECT_NAME = "YouTube Trending Analyzer"
VERSION = "1.0.0"

# ===== 数据路径 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

# 自动创建目录
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# 请求延迟（秒）- 避免被限流
REQUEST_DELAY = 2

# ===== 热度计算配置 =====
# 热度分数公式：(views * comments * likes_factor) / (hours_since_upload ^ decay)
POPULARITY_WEIGHTS = {
    "views": 1.0,           # 播放量权重
    "comments": 0.5,        # 评论数权重
    "likes": 0.3,           # 点赞数权重
    "time_decay": 0.5,      # 时间衰减指数（越小衰减越慢）
}

# ===== 输出配置 =====
EXPORT_FORMATS = ["csv", "json", "xlsx"]  # 导出格式
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ===== 日志配置 =====
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# 获取当前时间戳（用于文件名）
def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")
