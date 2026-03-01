from __future__ import annotations

import json
import logging
import os

from .schemas import CampaignExtract, DraftOutput
from .text_utils import detect_site_name, extract_hashtags, extract_keywords, extract_links, find_deadline

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    pass


def _openai_client():
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def heuristic_extract(text: str, source_url: str | None = None, site: str | None = None) -> CampaignExtract:
    hashtags = extract_hashtags(text)
    keywords = extract_keywords(text)
    links = extract_links(text)
    deadline = find_deadline(text)

    return CampaignExtract(
        source_url=source_url,
        site_name=site or detect_site_name(source_url),
        title=text.splitlines()[0][:120] if text.splitlines() else None,
        compensation={"type": "unknown", "notes": "heuristic fallback"},
        hashtags=hashtags,
        keywords=keywords,
        links={"purchase_links": links[:1], "reference_links": links[1:]},
        dates={"deadline": deadline},
        notes_for_notion="자동 추출(휴리스틱): 세부 내용 검토 필요",
        posting_plan="릴스 중심 + 필수 해시태그/고지문 반영",
    )


def extract_campaign(text: str, source_url: str | None = None, site: str | None = None, allow_heuristic: bool = False) -> CampaignExtract:
    prompt = f"""
너는 한국어 캠페인 공고를 구조화하는 정보추출기다.
아래 텍스트에서 인스타 협찬 캠페인 정보를 추출해 CampaignExtract JSON으로만 출력해.
- 헤딩 이름이 제각각이어도 의미를 파악해서 매핑.
- 날짜는 YYYY-MM-DD, 없으면 null.
- raw 본문 전체를 옮기지 말고 요약만 notes_for_notion/posting_plan에 넣어.
- required_disclosure 예시(#협찬/#광고)와 위치 규칙(본문 맨 앞 등)을 최대한 찾기.
- 확실치 않으면 null/unknown 사용.

입력 메타:
source_url={source_url}
site_name={site}

텍스트:
{text[:16000]}
""".strip()

    try:
        client = _openai_client()
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        content = response.output_text.strip()
        data = json.loads(content)
        if source_url and not data.get("source_url"):
            data["source_url"] = source_url
        if site and not data.get("site_name"):
            data["site_name"] = site
        return CampaignExtract.model_validate(data)
    except Exception as exc:
        if allow_heuristic:
            logger.warning("LLM extraction failed (%s). Falling back to heuristic.", exc)
            return heuristic_extract(text=text, source_url=source_url, site=site)
        raise LLMError(f"Extraction failed: {exc}") from exc


def generate_drafts(campaign: CampaignExtract, allow_heuristic: bool = False) -> DraftOutput:
    prompt = f"""
아래 캠페인 JSON을 바탕으로 인스타 릴스 스크립트와 캡션을 작성해.
페르소나: 20대 한국 여성, 생동감, 인간미, 완벽문장 지양, 짧은/긴 문장 혼합, 소소한 감탄사(ㅋㅋ/ㅎㅎ/사실/은근 좋더라).
컴플라이언스는 엄격히 지켜: #협찬 또는 #광고 표기를 규칙에 맞게 본문 상단에.
결과는 JSON으로만 출력:
{{"reels_script":"...", "instagram_caption":"..."}}

요구사항:
- reels_script: 시간코드(예: 0-3s) + 화면자막 + 말할대사.
- instagram_caption: 한국어 본문 + 맨 아래 영어 섹션 append.
- 필수 해시태그/키워드/금지사항 반영.

캠페인 JSON:
{campaign.model_dump_json(indent=2, ensure_ascii=False)}
""".strip()

    try:
        client = _openai_client()
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return DraftOutput.model_validate_json(response.output_text)
    except Exception as exc:
        if allow_heuristic:
            hashtags = " ".join(campaign.hashtags[:8])
            disclosure = "#협찬 #광고" if campaign.compliance.required_disclosure else ""
            reels = "0-3s 오프닝(제품 첫인상)\n3-10s 사용 장면 + 핵심 포인트\n10-15s 총평 + CTA"
            caption = (
                f"{disclosure}\n오늘 써보니까 사실 은근 좋더라 ㅎㅎ 핵심은 {', '.join(campaign.keywords[:3]) or '제품 포인트'}!\n"
                f"필수 확인 부탁드려요 ㅋㅋ\n\n{hashtags}\n\n[EN]\nSponsored review. Key points highlighted."
            ).strip()
            return DraftOutput(reels_script=reels, instagram_caption=caption)
        raise LLMError(f"Draft generation failed: {exc}") from exc
