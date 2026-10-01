# scripts/scraper.py
"""YouTube regional hot-list scraper.

YouTube removed the combined Trending tab in July 2025 (browseId FEtrending
now returns HTTP 400). This scraper still tries that endpoint and the HTML
feed first, then falls back to Innertube search filtered to videos uploaded
this week and sorted by view count for the requested region.
"""
import argparse
import json
import logging
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    COUNTRIES,
    LOG_FORMAT,
    LOG_LEVEL,
    MAX_RETRIES,
    MAX_VIDEOS_PER_REGION,
    NUM_WORKERS,
    PROXIES,
    PROXY_API_KEY,
    PROXY_API_URL,
    RAW_DATA_DIR,
    REQUEST_DELAY,
    REQUEST_TIMEOUT,
    RETRY_DELAY,
    SEARCH_VIEW_FILTER,
    USE_OFFICIAL_API,
    USE_PROXY_ROTATION,
    USER_AGENTS,
    YOUTUBE_API_KEY,
    get_timestamp,
)
from scripts.utils import parse_count, text_from_runs

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Public WEB client key embedded in youtube.com pages. Refreshed from the
# homepage when possible; this is not a user credential.
_FALLBACK_API_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
_FALLBACK_CLIENT_VERSION = "2.20250925.01.00"
_INNERTUBE_TIMEOUT = max(REQUEST_TIMEOUT, 25)


class YouTubeTrendingScraper:
    def __init__(self, use_proxy=None):
        self.session = requests.Session()
        self.base_url = "https://www.youtube.com"
        self.trending_url = "https://www.youtube.com/feed/trending"
        self.proxy_list = list(PROXIES)
        self.proxy_rotation_enabled = USE_PROXY_ROTATION if use_proxy is None else bool(use_proxy)
        self.use_proxy = self.proxy_rotation_enabled
        self.use_random_delay = False
        self.delay_range = (1, 5)
        self._proxy_index = 0
        self.api_key = _FALLBACK_API_KEY
        self.client_version = _FALLBACK_CLIENT_VERSION
        self._bootstrapped = False
        self._gl_notice = set()
        # YouTube has no CN storefront; HK is the Chinese-language chart that still returns videos.
        self.gl_overrides = {"CN": "HK"}

    def set_proxy_rotation(self, enabled=True, api_url=None):
        """Enable proxy rotation and optionally load proxies from an API."""
        self.proxy_rotation_enabled = bool(enabled)
        self.use_proxy = self.proxy_rotation_enabled
        url = api_url or PROXY_API_URL
        if url:
            self._load_proxies_from_api(url)

    def _load_proxies_from_api(self, url):
        if not url:
            logger.info("未配置 PROXY_API_URL，跳过代理 API")
            return
        headers = {}
        if PROXY_API_KEY:
            headers["Authorization"] = f"Bearer {PROXY_API_KEY}"
        try:
            response = self.session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            payload = response.json()
            proxies = payload.get("proxies") if isinstance(payload, dict) else payload
            if isinstance(proxies, list):
                self.proxy_list = [str(item) for item in proxies if item]
                logger.info("从代理 API 载入 %s 个代理", len(self.proxy_list))
        except Exception as exc:
            logger.warning("代理 API 不可用 (%s)，继续直连", exc)

    def _next_proxy(self):
        if not self.proxy_rotation_enabled or not self.proxy_list:
            return None
        proxy = self.proxy_list[self._proxy_index % len(self.proxy_list)]
        self._proxy_index += 1
        return {"http": proxy, "https": proxy}

    def _get_headers(self, language="en"):
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": f"{language},en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Referer": "https://www.youtube.com/",
            "Origin": "https://www.youtube.com",
        }

    def _request(self, method, url, retry_statuses=(429, 500, 502, 503, 504), **kwargs):
        kwargs.setdefault("timeout", _INNERTUBE_TIMEOUT)
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            proxies = self._next_proxy()
            if proxies:
                kwargs["proxies"] = proxies
            try:
                response = requests.request(method, url, **kwargs)
                if response.status_code in retry_statuses and attempt < MAX_RETRIES:
                    logger.warning("请求 %s 返回 %s，准备重试 (%s/%s)", url, response.status_code, attempt, MAX_RETRIES)
                    time.sleep(RETRY_DELAY)
                    continue
                return response
            except requests.RequestException as exc:
                last_error = exc
                logger.warning("请求失败 (%s/%s): %s", attempt, MAX_RETRIES, exc)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
        if last_error:
            raise last_error
        raise requests.RequestException(f"request failed: {url}")

    def _bootstrap(self):
        if self._bootstrapped:
            return
        self._bootstrapped = True
        try:
            response = self._request(
                "GET",
                self.base_url,
                headers=self._get_headers(),
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code != 200:
                return
            key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', response.text)
            version_match = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', response.text)
            if key_match:
                self.api_key = key_match.group(1)
            if version_match:
                self.client_version = version_match.group(1)
            logger.info("Innertube client %s", self.client_version)
        except Exception as exc:
            logger.warning("读取首页配置失败，使用内置 WEB client: %s", exc)

    def _content_gl(self, region):
        override = self.gl_overrides.get(region, region)
        if override != region and region not in self._gl_notice:
            self._gl_notice.add(region)
            logger.info(
                "YouTube 没有 %s 地区目录，改用 %s 图表，结果仍标记为 %s",
                region, override, region,
            )
        return override

    def _client(self, region):
        self._bootstrap()
        language = COUNTRIES.get(region, "en")
        return {
            "clientName": "WEB",
            "clientVersion": self.client_version,
            "hl": language,
            "gl": self._content_gl(region),
        }

    def _post_innertube(self, endpoint, payload, region):
        self._bootstrap()
        url = f"{self.base_url}/youtubei/v1/{endpoint}?key={self.api_key}&prettyPrint=false"
        headers = self._get_headers(COUNTRIES.get(region, "en"))
        headers["Content-Type"] = "application/json"
        headers["X-YouTube-Client-Name"] = "1"
        headers["X-YouTube-Client-Version"] = self.client_version
        response = self._request("POST", url, headers=headers, json=payload)
        if response.status_code == 400:
            logger.info("Innertube %s 返回 400（接口可能已下线）", endpoint)
            return None
        response.raise_for_status()
        return response.json()

    def scrape_trending(self, region="US"):
        """Scrape one region's hot list."""
        logger.info("开始爬取 %s 地区热榜...", region)
        videos = []
        try:
            if USE_OFFICIAL_API:
                if not YOUTUBE_API_KEY:
                    logger.error(
                        "USE_OFFICIAL_API 已开启，但环境变量 YOUTUBE_API_KEY 未设置。"
                        "跳过官方 API，改用 Innertube。"
                    )
                else:
                    videos = self._scrape_official_api(region)
            if not videos:
                videos = self._scrape_html(region)
            if not videos:
                videos = self._scrape_trending_browse(region)
            if not videos:
                videos = self._scrape_popular_search(region)
        except Exception as exc:
            logger.error("爬取 %s 失败: %s", region, exc)
            return []

        deduped = []
        seen = set()
        for video in videos:
            video_id = video.get("video_id")
            if not video_id or video_id in seen:
                continue
            seen.add(video_id)
            deduped.append(video)
            if len(deduped) >= MAX_VIDEOS_PER_REGION:
                break
        logger.info("成功获取 %s 个视频 (%s)", len(deduped), region)
        return deduped

    def _scrape_official_api(self, region):
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "regionCode": region,
            "maxResults": min(MAX_VIDEOS_PER_REGION, 50),
            "key": YOUTUBE_API_KEY,
        }
        response = self._request("GET", url, params=params, headers=self._get_headers(), timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            logger.warning("官方 API %s 失败: %s", region, response.status_code)
            return []
        videos = []
        for item in response.json().get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            videos.append({
                "video_id": item.get("id", ""),
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "views": int(stats.get("viewCount") or 0),
                "likes": int(stats.get("likeCount") or 0),
                "comments": int(stats.get("commentCount") or 0),
                "views_text": stats.get("viewCount", ""),
                "publish_time": snippet.get("publishedAt", ""),
                "publish_date": snippet.get("publishedAt", ""),
                "url": f"https://www.youtube.com/watch?v={item.get('id', '')}",
                "region": region,
                "source": "official_api",
                "scraped_at": datetime.now().isoformat(),
            })
        return videos

    def _scrape_html(self, region):
        language = COUNTRIES.get(region, "en")
        url = f"{self.trending_url}?gl={region}&hl={language}"
        response = self._request(
            "GET",
            url,
            headers=self._get_headers(language),
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            logger.warning("热榜页面 %s 状态码 %s", region, response.status_code)
            return []
        return self._extract_videos(response.text, region, source="html_trending")

    def _extract_videos(self, html_text, region, source="html"):
        """Parse embedded JSON, then fall back to BeautifulSoup anchors."""
        videos = self._extract_from_yt_initial_data(html_text, region, source)
        if videos:
            return videos
        videos = self._extract_with_beautifulsoup(html_text, region, source)
        if not videos:
            logger.warning("未找到视频数据 (%s)", region)
        return videos

    def _extract_from_yt_initial_data(self, html_text, region, source):
        match = re.search(r"ytInitialData\s*=\s*", html_text)
        if not match:
            return []
        try:
            data = json.loads(_extract_json_object(html_text, match.end()))
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("ytInitialData 解析失败: %s", exc)
            return []
        return self._videos_from_tree(data, region, source)[:MAX_VIDEOS_PER_REGION]

    def _extract_with_beautifulsoup(self, html_text, region, source):
        soup = BeautifulSoup(html_text, "lxml")
        videos = []
        seen = set()
        for anchor in soup.select("a[href*='/watch?v=']"):
            href = anchor.get("href") or ""
            found = re.search(r"v=([\w-]{11})", href)
            if not found:
                continue
            video_id = found.group(1)
            if video_id in seen:
                continue
            title = (anchor.get("title") or anchor.get_text(" ", strip=True) or "").strip()
            if not title or title.lower() in {"watch", "youtube"}:
                continue
            seen.add(video_id)
            videos.append(self._video_record(
                video_id=video_id,
                title=title,
                channel="",
                views_text="",
                publish_time="",
                region=region,
                source=source + "_bs4",
            ))
            if len(videos) >= MAX_VIDEOS_PER_REGION:
                break
        return videos

    def _scrape_trending_browse(self, region):
        """Legacy FEtrending kiosk. YouTube returns 400 since the tab was removed."""
        payload = {
            "context": {"client": self._client(region)},
            "browseId": "FEtrending",
            "params": "4gIOGgxtb3N0X3BvcHVsYXI=",
        }
        data = self._post_innertube("browse", payload, region)
        if not data:
            return []
        return self._videos_from_tree(data, region, "innertube_trending")

    def _scrape_popular_search(self, region):
        """Most-viewed videos uploaded this week, localized with gl/hl."""
        logger.info("%s 综合热榜不可用，改用本周播放量排序搜索", region)
        client = self._client(region)
        payload = {
            "context": {"client": client},
            "query": _region_query(region),
            "params": SEARCH_VIEW_FILTER,
        }
        data = self._post_innertube("search", payload, region)
        if not data:
            payload.pop("params", None)
            data = self._post_innertube("search", payload, region)
        if not data:
            return []
        videos = self._videos_from_tree(data, region, "search_week_views")
        if len(videos) < min(10, MAX_VIDEOS_PER_REGION):
            token = _find_continuation(data)
            if token:
                more = self._post_innertube(
                    "search",
                    {"context": {"client": client}, "continuation": token},
                    region,
                )
                if more:
                    videos.extend(self._videos_from_tree(more, region, "search_week_views"))
        return videos

    def _videos_from_tree(self, data, region, source):
        videos = []
        seen = set()
        for renderer in _walk_renderers(data):
            video = self._parse_renderer(renderer, region, source)
            if not video or video["video_id"] in seen:
                continue
            seen.add(video["video_id"])
            videos.append(video)
        return videos

    def _parse_renderer(self, renderer, region, source):
        if not isinstance(renderer, dict):
            return None
        if renderer.get("contentType") == "LOCKUP_CONTENT_TYPE_VIDEO" or "metadata" in renderer and "contentId" in renderer:
            return self._parse_lockup(renderer, region, source)
        video_id = renderer.get("videoId") or ""
        if not video_id:
            return None
        title = text_from_runs(renderer.get("title"))
        if not title:
            title = text_from_runs(renderer.get("headline"))
        if not title:
            return None
        channel = (
            text_from_runs(renderer.get("longBylineText"))
            or text_from_runs(renderer.get("shortBylineText"))
            or text_from_runs(renderer.get("ownerText"))
        )
        views_text = text_from_runs(renderer.get("viewCountText"))
        publish_time = text_from_runs(renderer.get("publishedTimeText")) or text_from_runs(renderer.get("publishedTimeText"))
        return self._video_record(video_id, title, channel, views_text, publish_time, region, source)

    def _parse_lockup(self, renderer, region, source):
        video_id = renderer.get("contentId") or renderer.get("videoId") or ""
        if not video_id:
            return None
        metadata = renderer.get("metadata") or {}
        title = text_from_runs(metadata.get("title")) or text_from_runs(renderer.get("title"))
        channel = ""
        metadata_rows = ((metadata.get("metadata") or {}).get("contentMetadataViewModel") or {}).get("metadataRows") or []
        for row in metadata_rows:
            parts = row.get("metadataParts") or []
            texts = [text_from_runs(part.get("text")) for part in parts]
            joined = " ".join(t for t in texts if t)
            if not channel and joined:
                channel = texts[0] if texts else joined
            if any(token in joined.lower() for token in ("view", "观看", "回", "vues")):
                views_text = joined
                break
        else:
            views_text = ""
        return self._video_record(video_id, title, channel, views_text, "", region, source)

    def _video_record(self, video_id, title, channel, views_text, publish_time, region, source):
        return {
            "video_id": video_id,
            "title": title or "",
            "channel": channel or "",
            "views": parse_count(views_text),
            "likes": 0,
            "comments": 0,
            "views_text": views_text or "",
            "publish_time": publish_time or "",
            "publish_date": "",
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "region": region,
            "source": source,
            "scraped_at": datetime.now().isoformat(),
        }

    def enrich_videos(self, videos, workers=None):
        """Fill likes (player) and comments (watch next) for scraped videos."""
        if not videos:
            return videos
        workers = max(1, min(workers or NUM_WORKERS, len(videos)))
        logger.info("补充点赞/评论：%s 个视频，%s 线程", len(videos), workers)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(self._enrich_one, video): video for video in videos}
            done = 0
            for future in as_completed(futures):
                done += 1
                try:
                    future.result()
                except Exception as exc:
                    logger.debug("补充详情失败: %s", exc)
                if done % 20 == 0 or done == len(videos):
                    logger.info("详情进度 %s/%s", done, len(videos))
        return videos

    def _enrich_one(self, video):
        region = video.get("region") or "US"
        video_id = video.get("video_id")
        if not video_id:
            return video
        client = self._client(region)
        # Newer WEB clients often answer player with LOGIN_REQUIRED and omit likes.
        player_client = dict(client)
        player_client["clientVersion"] = _FALLBACK_CLIENT_VERSION
        try:
            player = self._post_innertube(
                "player",
                {"context": {"client": player_client}, "videoId": video_id},
                region,
            )
        except Exception as exc:
            logger.debug("player %s 失败: %s", video_id, exc)
            player = None
        if player:
            details = player.get("videoDetails") or {}
            micro = ((player.get("microformat") or {}).get("playerMicroformatRenderer") or {})
            view_count = details.get("viewCount") or micro.get("viewCount")
            like_count = details.get("likeCount") or micro.get("likeCount")
            if view_count:
                video["views"] = parse_count(view_count)
                video["views_text"] = str(view_count)
            if like_count:
                video["likes"] = parse_count(like_count)
            if details.get("author") and not video.get("channel"):
                video["channel"] = details.get("author")
            if (details.get("title") or micro.get("title")) and not video.get("title"):
                title_node = details.get("title") or micro.get("title")
                video["title"] = title_node if isinstance(title_node, str) else text_from_runs(title_node)
            publish_date = micro.get("publishDate") or micro.get("uploadDate") or ""
            if publish_date:
                video["publish_date"] = publish_date
            length = details.get("lengthSeconds")
            if length is not None:
                try:
                    video["length_seconds"] = int(length)
                except (TypeError, ValueError):
                    pass
        try:
            nxt = self._post_innertube(
                "next",
                {"context": {"client": client}, "videoId": video_id},
                region,
            )
        except Exception as exc:
            logger.debug("next %s 失败: %s", video_id, exc)
            nxt = None
        if nxt:
            comments = _comment_count(nxt)
            if comments:
                video["comments"] = comments
        return video

    def _sleep_between_regions(self):
        if self.use_random_delay:
            time.sleep(random.uniform(*self.delay_range))
        elif REQUEST_DELAY:
            time.sleep(REQUEST_DELAY)

    def scrape_all_regions(self, regions=None):
        selected = list(regions) if regions else list(COUNTRIES.keys())
        unknown = [code for code in selected if code not in COUNTRIES]
        if unknown:
            logger.warning("未知地区代码将被忽略: %s", ", ".join(unknown))
            selected = [code for code in selected if code in COUNTRIES]
        all_videos = []
        for index, region in enumerate(selected):
            all_videos.extend(self.scrape_trending(region))
            if index < len(selected) - 1:
                self._sleep_between_regions()
        if all_videos:
            self._bootstrap()
            self.enrich_videos(all_videos)
            missing = [video for video in all_videos if not video.get("likes")]
            if missing:
                logger.info("点赞缺失 %s 条，降低并发重试", len(missing))
                self.enrich_videos(missing, workers=2)
        return all_videos


def _extract_json_object(text, start):
    if start >= len(text) or text[start] != "{":
        raise ValueError("JSON object not found")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise ValueError("unterminated JSON object")


def _walk_renderers(node):
    if isinstance(node, dict):
        for key in ("gridVideoRenderer", "videoRenderer", "compactVideoRenderer", "reelItemRenderer"):
            child = node.get(key)
            if isinstance(child, dict) and child.get("videoId"):
                yield child
        lockup = node.get("lockupViewModel")
        if isinstance(lockup, dict):
            yield lockup
        for value in node.values():
            yield from _walk_renderers(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_renderers(item)


def _find_continuation(node):
    if isinstance(node, dict):
        command = node.get("continuationCommand")
        if isinstance(command, dict) and command.get("token"):
            return command["token"]
        for value in node.values():
            found = _find_continuation(value)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_continuation(item)
            if found:
                return found
    return None


def _comment_count(data):
    panels = data.get("engagementPanels") or []
    for panel in panels:
        renderer = (panel or {}).get("engagementPanelSectionListRenderer") or {}
        header = ((renderer.get("header") or {}).get("engagementPanelTitleHeaderRenderer") or {})
        text = text_from_runs(header.get("contextualInfo"))
        if text:
            return parse_count(text)
    return 0



_REGION_QUERIES = {
    "US": "the",
    "GB": "and",
    "JP": "の",
    "IN": "का",
    "BR": "não",
    "DE": "und",
    "FR": "les",
    "CN": "的",
    "KR": "의",
    "MX": "que",
}


def _region_query(region):
    return _REGION_QUERIES.get(region, "the")


def _parse_regions(value):
    if not value:
        return None
    return [part.strip().upper() for part in value.split(",") if part.strip()]


def main():
    parser = argparse.ArgumentParser(description="抓取多地区 YouTube 热榜")
    parser.add_argument("--regions", help="逗号分隔的地区代码，例如 US,JP,IN")
    parser.add_argument("--log-level", default=None, help="DEBUG/INFO/WARNING/ERROR")
    args = parser.parse_args()
    if args.log_level:
        logging.getLogger().setLevel(args.log_level.upper())

    scraper = YouTubeTrendingScraper()
    videos = scraper.scrape_all_regions(_parse_regions(args.regions))
    output_file = os.path.join(RAW_DATA_DIR, f"raw_videos_{get_timestamp()}.json")
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(videos, handle, ensure_ascii=False, indent=2)
    logger.info("数据已保存到 %s（%s 条）", output_file, len(videos))
    return videos


if __name__ == "__main__":
    main()
