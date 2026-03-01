from campaign_ingest.schemas import CampaignExtract


def test_campaign_schema_validation():
    data = {
        "source_url": "https://example.com/campaign",
        "site_name": "example.com",
        "title": "테스트 캠페인",
        "brand_or_vendor": "브랜드",
        "product_name": "제품A",
        "compensation": {"type": "mixed", "amount_krw": 10000, "points": 3000, "notes": "제품+포인트"},
        "required_channels": ["Instagram Reels"],
        "mission_guidelines": {"must_do": ["릴스 업로드"], "nice_to_have": [], "forbidden": [], "reels_guide": [], "review_guide": []},
        "compliance": {"required_disclosure": True, "required_disclosure_examples": ["#협찬"], "placement_rules": ["본문 맨 앞"]},
        "hashtags": ["#협찬"],
        "keywords": ["키워드"],
        "links": {"purchase_links": ["https://example.com"], "reference_links": []},
        "dates": {"deadline": "2026-03-20"},
        "notes_for_notion": "요약",
        "posting_plan": "포스팅 요약",
    }
    parsed = CampaignExtract.model_validate(data)
    assert parsed.compensation.type == "mixed"
    assert parsed.dates.deadline == "2026-03-20"
