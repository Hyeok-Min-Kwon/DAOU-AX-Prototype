"""
캠페인 데이터 스키마 (Pydantic v2)
==================================

3개 모델로 분리:
- `CampaignInput`  — 캠페인 조건 (사용자가 발송 전에 결정하는 것). API 예측 요청에 재사용.
- `CampaignOutcome` — 캠페인 결과 KPI 3종 (open/click/conversion).
- `CampaignRecord`  — 학습 데이터 한 행 = Input + Outcome. generator 출력 단위.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.data.patterns import (
    MAX_VOLUME,
    MIN_VOLUME,
    AgeGroup,
    CampaignPurpose,
    Category,
    MessageType,
    Region,
)


class CampaignInput(BaseModel):
    """캠페인 발송 조건. API 예측 요청에도 그대로 재사용된다."""

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    category: Category
    send_datetime: datetime
    hour: int = Field(ge=0, le=23, description="0~23, send_datetime에서 파생")
    weekday: int = Field(ge=0, le=6, description="월=0 ~ 일=6, send_datetime에서 파생")
    message_type: MessageType
    purpose: CampaignPurpose
    target_age: AgeGroup
    target_region: Region
    volume: int = Field(ge=MIN_VOLUME, le=MAX_VOLUME)

    @model_validator(mode="after")
    def _check_derived_time_fields(self) -> "CampaignInput":
        """`hour`/`weekday`가 `send_datetime`과 일치하는지 보장."""
        if self.hour != self.send_datetime.hour:
            raise ValueError(
                f"hour({self.hour}) != send_datetime.hour({self.send_datetime.hour})"
            )
        if self.weekday != self.send_datetime.weekday():
            raise ValueError(
                f"weekday({self.weekday}) != send_datetime.weekday()"
                f"({self.send_datetime.weekday()})"
            )
        return self


class CampaignOutcome(BaseModel):
    """캠페인 KPI. 깔때기 관계: open_rate > click_rate > conversion_rate."""

    model_config = ConfigDict(extra="forbid")

    open_rate: float = Field(ge=0.0, le=1.0)
    click_rate: float = Field(ge=0.0, le=1.0)
    conversion_rate: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _check_funnel_order(self) -> "CampaignOutcome":
        if not (self.open_rate >= self.click_rate >= self.conversion_rate):
            raise ValueError(
                "Funnel order violated: expected "
                f"open({self.open_rate}) >= click({self.click_rate}) "
                f">= conversion({self.conversion_rate})"
            )
        return self


class CampaignRecord(CampaignInput, CampaignOutcome):
    """학습 데이터 한 행 = Input + Outcome. generator 출력의 단위."""

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    campaign_id: str
