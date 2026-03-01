from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .crawler import CrawlError, crawl_campaign_text
from .llm import extract_campaign, generate_drafts
from .notion_client import build_notion_properties, create_database_row, load_config
from .text_utils import detect_site_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Campaign ingest automation")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="Campaign URL")
    src.add_argument("--paste-file", help="Raw pasted text file")
    parser.add_argument("--site", help="Optional site name")
    parser.add_argument("--dry-run", action="store_true", help="Print outputs only")
    parser.add_argument("--json-output", help="Path to write extracted JSON + drafts")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def _load_input(url: str | None, paste_file: str | None) -> tuple[str, str | None]:
    if url:
        text, _ = crawl_campaign_text(url)
        return text, url
    path = Path(paste_file or "")
    if not path.exists():
        raise FileNotFoundError(f"Paste file not found: {path}")
    return path.read_text(encoding="utf-8"), None


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    try:
        text, source_url = _load_input(args.url, args.paste_file)
    except CrawlError as exc:
        logging.error(str(exc))
        raise SystemExit(2)

    site = args.site or detect_site_name(source_url)
    campaign = extract_campaign(text=text, source_url=source_url, site=site, allow_heuristic=args.dry_run)
    drafts = generate_drafts(campaign=campaign, allow_heuristic=args.dry_run)

    config = load_config(args.config)
    notion_props = build_notion_properties(campaign, config)

    output = {
        "campaign_extract": campaign.model_dump(),
        "drafts": drafts.model_dump(),
        "notion_payload": notion_props,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))

    if args.json_output:
        Path(args.json_output).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.dry_run:
        logging.info("Dry-run: Notion API call skipped")
        return

    response = create_database_row(campaign, config)
    logging.info("Notion row created: %s", response.get("id"))


if __name__ == "__main__":
    main()
