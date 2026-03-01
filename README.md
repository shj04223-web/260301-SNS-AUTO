# campaign-ingest

Instagram sponsorship campaign automation (today scope): crawl or pasted text -> LLM extraction -> Notion DB row + Instagram draft outputs.

## Features
- Input from URL (`--url`) or pasted text file (`--paste-file`)
- Robust extraction into strict `CampaignExtract` schema (Pydantic)
- Notion row creation for **CO-WORK LIST** style mapping
- Generates:
  - Instagram Reels draft script (time-coded beats + on-screen captions)
  - Instagram caption (Korean main + English section)
- `--dry-run` mode prints JSON + Notion payload without API write
- Login wall detection (`LOGIN_REQUIRED`)
- JS-render fallback via Playwright (optional dependency)

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[test]
```

Optional JS-rendering:
```bash
pip install -e .[playwright]
playwright install chromium
```

Create `.env` or export env vars:
```bash
export OPENAI_API_KEY="..."
export NOTION_TOKEN="..."
export NOTION_DATABASE_ID="..."
```

## Config
`config/config.yaml`
- `notion.database_id`: can be direct ID or `${NOTION_DATABASE_ID}` placeholder
- `property_mapping`:
  - `deadline` -> `마감일`
  - `vendor` -> `체험단업체`
  - `status` -> `진행상태` (always set to `크롤링검토필요`)
  - `campaign_info` -> `캠페인정보`
  - `posting_info` -> `포스팅 정보`

## Run
URL mode:
```bash
python -m campaign_ingest --url "https://example.com/campaign" --dry-run
```

Paste mode:
```bash
python -m campaign_ingest --paste-file samples/stylec_like.txt --dry-run
```

Save output JSON:
```bash
python -m campaign_ingest --paste-file samples/reviewplace_like.txt --dry-run --json-output out.json
```

## Tests
```bash
pytest -q
```

## Troubleshooting
- `LOGIN_REQUIRED`: campaign page needs auth; use pasted text instead.
- `JS_RENDER_REQUIRED`: install playwright optional deps and browser.
- Missing `OPENAI_API_KEY`: in `--dry-run`, app falls back to heuristic extraction/draft generation; in normal mode this is an error.
- Notion write errors: verify `NOTION_TOKEN`, database share permissions, and property names in `config/config.yaml`.

## Notes
- Raw page text is **never** sent to Notion payload.
- Property `진행상태` is always fixed to `크롤링검토필요`.
