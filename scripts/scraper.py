# scripts/scraper.py
import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from datetime import datetime
import random
import sys
import os
import re

# 导入配置
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class YouTubeTrendingScraper:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.youtube.com"
        self.trending_url = "https://www.youtube.com/feed/trending"
        
    def _get_headers(self):
        """获取随机 User-Agent"""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.youtube.com/",
        }
    
    def scrape_trending(self, region="US"):
        """
        爬取指定地区的 YouTube 热榜
        
        Args:
            region: 国家代码 (US, JP, IN, etc.)
            
        Returns:
            list: 热榜视频列表
        """
        logger.info(f"开始爬取 {region} 地区热榜...")
        
        try:
            # 构造 URL
            url = f"{self.trending_url}?gl={region}&hl={COUNTRIES.get(region, 'en')}"
            
            # 发送请求
            headers = self._get_headers()
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 解析 HTML
            soup = BeautifulSoup(response.content, 'lxml')
            
            # 提取视频列表（这里用 yt-initial-data 从 JSON 提取）
            videos = self._extract_videos(response.text, region)
            
            logger.info(f"成功获取 {len(videos)} 个视频")
            return videos
            
        except Exception as e:
            logger.error(f"爬取 {region} 失败: {str(e)}")
            return []
    
    def _extract_videos(self, html_text, region):
        """从 HTML 中提取视频信息"""
        videos = []
        
        try:
            # YouTube 将数据以 JSON 形式嵌入在 HTML 中
            # 寻找 ytInitialData
            match = re.search(r'var ytInitialData = ({.*?});', html_text)
            if not match:
                logger.warning("未找到视频数据")
                return videos
            
            data = json.loads(match.group(1))
            
            # 导航到视频列表
            tabs = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])
            
            for tab in tabs:
                tab_content = tab.get('tabRenderer', {}).get('content', {})
                section_list = tab_content.get('sectionListRenderer', {}).get('contents', [])
                
                for section in section_list:
                    item_section = section.get('itemSectionRenderer', {}).get('contents', [])
                    
                    for item in item_section:
                        grid_renderer = item.get('gridRenderer', {})
                        grid_items = grid_renderer.get('items', [])
                        
                        for grid_item in grid_items:
                            video_info = self._parse_grid_item(grid_item, region)
                            if video_info:
                                videos.append(video_info)
            
            return videos[:50]  # 返回前 50 个
            
        except Exception as e:
            logger.error(f"解析视频数据失败: {str(e)}")
            return videos
    
    def _parse_grid_item(self, item, region):
        """解析单个视频信息"""
        try:
            renderer = item.get('gridVideoRenderer', {})
            
            if not renderer:
                return None
            
            video_id = renderer.get('videoId', '')
            
            # 标题
            title_runs = renderer.get('title', {}).get('runs', [])
            title = ''.join([run.get('text', '') for run in title_runs])
            
            # 频道名称
            channel_runs = renderer.get('longBylineText', {}).get('runs', [])
            channel = ''.join([run.get('text', '') for run in channel_runs])
            
            # 视图数
            views_text = renderer.get('viewCountText', {}).get('simpleText', '')
            views = self._parse_count(views_text)
            
            # 发布时间
            publish_time = renderer.get('publishedTimeText', {}).get('simpleText', '')
            
            return {
                'video_id': video_id,
                'title': title,
                'channel': channel,
                'views': views,
                'views_text': views_text,
                'publish_time': publish_time,
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'region': region,
                'scraped_at': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.debug(f"解析视频项失败: {str(e)}")
            return None
    
    def _parse_count(self, text):
        """将 YouTube 的数字文本转换为整数"""
        try:
            text = text.lower().strip()
            
            if 'k' in text:
                return int(float(text.replace('k', '')) * 1000)
            elif 'm' in text:
                return int(float(text.replace('m', '')) * 1000000)
            elif 'b' in text:
                return int(float(text.replace('b', '')) * 1000000000)
            else:
                return int(''.join(filter(str.isdigit, text))) or 0
        except:
            return 0
    
    def scrape_all_regions(self):
        """爬取所有支持的地区"""
        all_videos = []
        
        for region in COUNTRIES.keys():
            videos = self.scrape_trending(region)
            all_videos.extend(videos)
            
            # 延迟，避免被限流
            time.sleep(REQUEST_DELAY)
        
        return all_videos

def main():
    scraper = YouTubeTrendingScraper()
    videos = scraper.scrape_all_regions()
    
    # 保存原始数据
    output_file = os.path.join(RAW_DATA_DIR, f"raw_videos_{get_timestamp()}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
    
    logger.info(f"数据已保存到 {output_file}")
    return videos

if __name__ == "__main__":
    main()
