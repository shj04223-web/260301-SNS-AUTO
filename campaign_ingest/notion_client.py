from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import requests
import yaml

from .schemas import CampaignExtract

logger = logging.getLogger(__name__)


class NotionClientError(RuntimeError):
    pass


def load_config(path: str = "config/config.yaml") -> dict[str, Any]:
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise NotionClientError(f"Config not found: {path}")
    config = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    db_id = config.get("notion", {}).get("database_id")
    if isinstance(db_id, str) and db_id.strip() == "${NOTION_DATABASE_ID}":
        config["notion"]["database_id"] = os.getenv("NOTION_DATABASE_ID")
    return config


def _rich_text(value: str) -> dict[str, Any]:
    return {"rich_text": [{"text": {"content": value[:1900]}}]}


def _title_text(value: str) -> dict[str, Any]:
    return {"title": [{"text": {"content": value[:1900]}}]}


def build_notion_properties(campaign: CampaignExtract, config: dict[str, Any]) -> dict[str, Any]:
    mapping = config["notion"]["property_mapping"]
    props: dict[str, Any] = {}

    deadline_prop = mapping["deadline"]
    if campaign.dates.deadline:
        props[deadline_prop] = {"date": {"start": campaign.dates.deadline}}

    vendor_prop = mapping["vendor"]
    if campaign.brand_or_vendor:
        vendor_type = config["notion"].get("vendor_property_type", "rich_text")
        props[vendor_prop] = _title_text(campaign.brand_or_vendor) if vendor_type == "title" else _rich_text(campaign.brand_or_vendor)

    status_prop = mapping["status"]
    props[status_prop] = {"select": {"name": "크롤링검토필요"}}

    info_prop = mapping["campaign_info"]
    posting_prop = mapping["posting_info"]
    props[info_prop] = _rich_text(campaign.notes_for_notion or "자동 추출 결과 확인 필요")
    props[posting_prop] = _rich_text(campaign.posting_plan or "인스타 릴스 중심 초안 생성")

    return props


def create_database_row(campaign: CampaignExtract, config: dict[str, Any]) -> dict[str, Any]:
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = config["notion"].get("database_id")
    if not database_id:
        raise NotionClientError("NOTION_DATABASE_ID missing in config/config.yaml")
    if not notion_token:
        raise NotionClientError("NOTION_TOKEN env var is required")

    payload = {
        "parent": {"database_id": database_id},
        "properties": build_notion_properties(campaign, config),
    }
    logger.info("Creating Notion database row")
    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers={
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )
    if res.status_code >= 300:
        raise NotionClientError(f"Notion API error {res.status_code}: {res.text}")
    return res.json()
