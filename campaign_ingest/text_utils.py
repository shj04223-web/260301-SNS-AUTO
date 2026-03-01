from __future__ import annotations

import re
from urllib.parse import urlparse

from dateutil import parser


HASHTAG_PATTERN = re.compile(r"(?<!\w)#([0-9A-Za-z가-힣_]+)")
URL_PATTERN = re.compile(r"https?://[^\s)]+")


def detect_site_name(url: str | None) -> str | None:
    if not url:
        return None
    host = urlparse(url).netloc.lower()
    if not host:
        return None
    return host.replace("www.", "")


def extract_hashtags(text: str) -> list[str]:
    tags = [f"#{m.group(1)}" for m in HASHTAG_PATTERN.finditer(text)]
    return list(dict.fromkeys(tags))


def extract_keywords(text: str) -> list[str]:
    keywords: list[str] = []
    for line in text.splitlines():
        lower = line.lower()
        if "키워드" in line or "keyword" in lower:
            candidates = re.split(r"[,/|•·]|\s{2,}", line)
            for c in candidates:
                cleaned = c.strip(" -:\t")
                if cleaned and "키워드" not in cleaned and len(cleaned) > 1:
                    keywords.append(cleaned)
    return list(dict.fromkeys(keywords))


def extract_links(text: str) -> list[str]:
    return list(dict.fromkeys(URL_PATTERN.findall(text)))


def normalize_date(date_str: str) -> str | None:
    try:
        dt = parser.parse(date_str, fuzzy=True, dayfirst=False)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def find_deadline(text: str) -> str | None:
    for line in text.splitlines():
        if any(k in line for k in ["마감", "등록", "deadline", "리뷰"]):
            normalized = normalize_date(line)
            if normalized:
                return normalized
    return None
