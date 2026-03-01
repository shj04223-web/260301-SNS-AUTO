from pathlib import Path

from campaign_ingest.llm import heuristic_extract


def test_extract_hashtags_keywords_stylec_sample():
    text = Path("samples/stylec_like.txt").read_text(encoding="utf-8")
    parsed = heuristic_extract(text)
    assert "#누벨라뷰" in parsed.hashtags
    assert any("저자극" in k for k in parsed.keywords)


def test_extract_hashtags_keywords_reviewplace_sample():
    text = Path("samples/reviewplace_like.txt").read_text(encoding="utf-8")
    parsed = heuristic_extract(text)
    assert "#브루데이" in parsed.hashtags
    assert any("산미적당" in k for k in parsed.keywords)
