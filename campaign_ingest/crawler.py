from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

LOGIN_WALL_HINTS = ["로그인", "login", "sign in", "회원가입"]


class CrawlError(RuntimeError):
    pass


def _is_login_wall(html: str) -> bool:
    lower = html.lower()
    contains_hint = any(h in lower for h in LOGIN_WALL_HINTS)
    has_password_input = "type=\"password\"" in lower or "type='password'" in lower
    return contains_hint and has_password_input


def _extract_text_bs4(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return "\n".join(s.strip() for s in soup.stripped_strings)


def _extract_text_trafilatura(html: str) -> str | None:
    try:
        import trafilatura

        return trafilatura.extract(html, include_links=True, include_comments=False)
    except Exception:
        return None


def _fetch_playwright(url: str, timeout: int = 25000) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise CrawlError(
            "JS_RENDER_REQUIRED: install optional dependency `pip install campaign-ingest[playwright]` "
            "and run `playwright install chromium`."
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=timeout)
        html = page.content()
        browser.close()
        return html


def crawl_campaign_text(url: str, timeout: int = 20) -> tuple[str, str]:
    logger.info("Fetching URL: %s", url)
    res = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    res.raise_for_status()

    html = res.text
    if _is_login_wall(html):
        raise CrawlError("LOGIN_REQUIRED")

    text = _extract_text_trafilatura(html) or _extract_text_bs4(html)
    if len(text.strip()) < 300:
        logger.info("Low text extracted; trying JS-render fallback")
        html = _fetch_playwright(url)
        if _is_login_wall(html):
            raise CrawlError("LOGIN_REQUIRED")
        text = _extract_text_trafilatura(html) or _extract_text_bs4(html)

    if not text.strip():
        raise CrawlError("EMPTY_CONTENT")

    return text, html
