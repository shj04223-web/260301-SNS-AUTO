from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Compensation(BaseModel):
    type: Literal["product", "payback", "points", "mixed", "unknown"] = "unknown"
    amount_krw: int | None = None
    points: int | None = None
    notes: str | None = None


class MissionGuidelines(BaseModel):
    must_do: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)
    reels_guide: list[str] = Field(default_factory=list)
    review_guide: list[str] = Field(default_factory=list)


class Compliance(BaseModel):
    required_disclosure: bool = False
    required_disclosure_examples: list[str] = Field(default_factory=list)
    placement_rules: list[str] = Field(default_factory=list)


class Links(BaseModel):
    purchase_links: list[str] = Field(default_factory=list)
    reference_links: list[str] = Field(default_factory=list)


class Dates(BaseModel):
    apply_start: str | None = None
    apply_end: str | None = None
    announce_date: str | None = None
    review_start: str | None = None
    review_end: str | None = None
    deadline: str | None = None


class CampaignExtract(BaseModel):
    source_url: str | None = None
    site_name: str | None = None
    title: str | None = None
    brand_or_vendor: str | None = None
    product_name: str | None = None
    compensation: Compensation = Field(default_factory=Compensation)
    required_channels: list[str] = Field(default_factory=list)
    mission_guidelines: MissionGuidelines = Field(default_factory=MissionGuidelines)
    compliance: Compliance = Field(default_factory=Compliance)
    hashtags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    links: Links = Field(default_factory=Links)
    dates: Dates = Field(default_factory=Dates)
    notes_for_notion: str = ""
    posting_plan: str = ""


class DraftOutput(BaseModel):
    reels_script: str
    instagram_caption: str
