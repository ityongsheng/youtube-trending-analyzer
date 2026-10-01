"""Shared parsing helpers for counts, relative times, and text runs."""
import re
from datetime import datetime, timezone

_COUNT_WORDS = re.compile(
    r"(views?|watching|次观看|次播放|回視聴|회|visualizaç(?:ões|oes)|visualizaciones|vues|aufrufe|views)",
    re.IGNORECASE,
)


def text_from_runs(node):
    """Extract visible text from a YouTube simpleText / runs node."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, (int, float)):
        return str(node)
    if not isinstance(node, dict):
        return ""
    if "simpleText" in node and isinstance(node["simpleText"], str):
        return node["simpleText"]
    runs = node.get("runs") or []
    return "".join(run.get("text", "") for run in runs if isinstance(run, dict))


def _to_float(number):
    """Parse a localized number. '1,1' is 1.1; '1,234' and '1,234,567' are thousands."""
    number = re.sub(r"[^0-9.,]", "", str(number))
    if not number:
        return 0.0
    if "," in number and "." in number:
        if number.rfind(",") < number.rfind("."):
            number = number.replace(",", "")
        else:
            number = number.replace(".", "").replace(",", ".")
    elif number.count(",") > 1:
        number = number.replace(",", "")
    elif "," in number:
        head, tail = number.split(",", 1)
        if len(tail) == 3 and tail.isdigit():
            number = head + tail
        else:
            number = head + "." + tail
    elif number.count(".") > 1:
        number = number.replace(".", "")
    try:
        return float(number)
    except ValueError:
        return 0.0


def parse_count(text):
    """Convert YouTube count text (1.2M / 3.4万 / 1,1 mil / 1,234) to int."""
    if text is None:
        return 0
    if isinstance(text, bool):
        return int(text)
    if isinstance(text, (int, float)):
        return int(text)
    raw = str(text).replace("\u00a0", " ").replace("\xa0", " ").strip()
    if not raw:
        return 0
    raw = _COUNT_WORDS.sub("", raw)
    raw = raw.lower().strip()
    word_suffixes = [
        ("亿", 100_000_000),
        ("億", 100_000_000),
        ("억", 100_000_000),
        ("万", 10_000),
        ("萬", 10_000),
        ("만", 10_000),
        ("milhões", 1_000_000),
        ("milhoes", 1_000_000),
        ("milhão", 1_000_000),
        ("milhao", 1_000_000),
        ("millones", 1_000_000),
        ("millions", 1_000_000),
        ("million", 1_000_000),
        ("billions", 1_000_000_000),
        ("billion", 1_000_000_000),
        ("thousands", 1_000),
        ("thousand", 1_000),
        ("mille", 1_000),
        ("mil", 1_000),
    ]
    for suffix, factor in word_suffixes:
        if suffix in raw:
            number = raw.split(suffix, 1)[0]
            return int(_to_float(number) * factor)
    letter = re.search(r"([0-9][0-9.,]*)\s*([kmb])(?![a-z])", raw)
    if letter:
        factor = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}[letter.group(2)]
        return int(_to_float(letter.group(1)) * factor)
    return int(_to_float(raw))



_RELATIVE_UNITS = [
    (re.compile(r"(\d+)\s*(?:seconds?|secs?|segundos?|秒)"), lambda n: n / 3600),
    (re.compile(r"(\d+)\s*(?:minutes?|mins?|minutos?|分钟|分鐘|分|मिनट)"), lambda n: n / 60),
    (re.compile(r"(\d+)\s*(?:hours?|hrs?|horas?|heures?|stunden?|小时|小時|時間|시간|घंटे|घंटा)"), lambda n: float(n)),
    (re.compile(r"(\d+)\s*(?:days?|d[ií]as?|dias?|jours?|tage?|天|日|일|दिन)"), lambda n: n * 24),
    (re.compile(r"(\d+)\s*(?:weeks?|semanas?|semaines?|wochen?|周|週|주|हफ्ते|हफ्ता)"), lambda n: n * 24 * 7),
    (re.compile(r"(\d+)\s*(?:months?|meses|mois|monate?|个月|個月|ヶ月|달|महीने|महीना)"), lambda n: n * 24 * 30),
    (re.compile(r"(\d+)\s*(?:years?|a[nñ]os?|anos?|jahre?|年|년|साल)"), lambda n: n * 24 * 365),
]


def hours_from_relative(text):
    """Parse '2 hours ago' / '3天前' into hours. None if unrecognized."""
    if not text:
        return None
    sample = str(text).strip().lower()
    for pattern, convert in _RELATIVE_UNITS:
        match = pattern.search(sample)
        if match:
            return max(float(convert(float(match.group(1)))), 0.5)
    return None


def hours_from_iso(value):
    """Hours between an ISO timestamp and now (UTC)."""
    if not value:
        return None
    try:
        text = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
        return max(delta.total_seconds() / 3600, 0.5)
    except (ValueError, TypeError):
        return None


def resolve_hours(video):
    """Prefer an explicit hour count, then ISO publish date, then relative text."""
    if isinstance(video, dict):
        getter = video.get
    else:
        getter = video.get if hasattr(video, "get") else lambda k, d=None: d

    explicit = getter("hours_since_upload", None)
    if explicit not in (None, ""):
        try:
            return max(float(explicit), 0.5)
        except (TypeError, ValueError):
            pass
    iso_hours = hours_from_iso(getter("publish_date", None))
    if iso_hours is not None:
        return iso_hours
    relative = hours_from_relative(getter("publish_time", ""))
    if relative is not None:
        return relative
    return 1.0
