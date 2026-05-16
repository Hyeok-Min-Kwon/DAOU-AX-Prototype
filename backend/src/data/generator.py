"""
합성 캠페인 데이터 생성기
========================

`patterns.py`의 도메인 가정을 사용해 학습용 데이터(`CampaignRecord` 행)를 만든다.

전환율 계산 공식:
    conversion = base_rate
                 * hour_weight        (업종별 시간대 효과)
                 * weekday_weight     (업종별 요일 효과)
                 * category_type_boost (업종 × 메시지 타입 상성)
                 * purpose_multiplier  (캠페인 목적)
                 * age_multiplier      (연령대)
                 * age_type_multiplier (연령 × 메시지 타입)
                 * region_multiplier   (지역)
                 * gaussian_noise      (자연 변동)

깔때기 비율:
    click_rate = conversion * U(3, 5)
    open_rate  = click_rate * U(5, 10)
"""

from datetime import datetime, timedelta
from uuid import uuid4

import numpy as np
import pandas as pd

from src.data.patterns import (
    AGE_MULTIPLIER,
    AGE_TYPE_MULTIPLIER,
    CATEGORY_TYPE_BOOST,
    CONVERSION_RATE_NOISE_STD,
    HOUR_WEIGHTS_BY_CATEGORY,
    MAX_VOLUME,
    MIN_VOLUME,
    PURPOSE_MULTIPLIER,
    REGION_MULTIPLIER,
    TYPE_BASE_CONVERSION_RATE,
    WEEKDAY_WEIGHTS_BY_CATEGORY,
    AgeGroup,
    CampaignPurpose,
    Category,
    MessageType,
    Region,
)


def _compute_conversion_rate(
    rng: np.random.Generator,
    category: Category,
    hour: int,
    weekday: int,
    message_type: MessageType,
    purpose: CampaignPurpose,
    age: AgeGroup,
    region: Region,
) -> float:
    base = TYPE_BASE_CONVERSION_RATE[message_type]
    hour_w = HOUR_WEIGHTS_BY_CATEGORY[category][hour]
    weekday_w = WEEKDAY_WEIGHTS_BY_CATEGORY[category][weekday]
    cat_type_boost = CATEGORY_TYPE_BOOST.get(category, {}).get(message_type, 1.0)
    purpose_mult = PURPOSE_MULTIPLIER[purpose]
    age_mult = AGE_MULTIPLIER[age]
    age_type_mult = AGE_TYPE_MULTIPLIER.get(age, {}).get(message_type, 1.0)
    region_mult = REGION_MULTIPLIER[region]

    # 자연 변동: 평균 1.0, 표준편차 CONVERSION_RATE_NOISE_STD인 가우시안
    noise = max(0.0, rng.normal(loc=1.0, scale=CONVERSION_RATE_NOISE_STD))

    conv = (
        base
        * hour_w
        * weekday_w
        * cat_type_boost
        * purpose_mult
        * age_mult
        * age_type_mult
        * region_mult
        * noise
    )
    return float(np.clip(conv, 0.0, 1.0))


def _sample_enum(rng: np.random.Generator, enum_cls):
    values = list(enum_cls)
    return values[int(rng.integers(0, len(values)))]


def generate_dataset(
    n: int,
    start: datetime,
    end: datetime,
    seed: int = 42,
) -> pd.DataFrame:
    """`n`개의 캠페인을 합성하여 DataFrame으로 반환."""
    rng = np.random.default_rng(seed)
    total_seconds = int((end - start).total_seconds())

    rows = []
    for _ in range(n):
        # 발송 시각: 균등 무작위. 시간대·요일 패턴은 전환율에만 반영됨.
        offset = int(rng.integers(0, total_seconds))
        send_dt = (start + timedelta(seconds=offset)).replace(
            minute=0, second=0, microsecond=0
        )
        hour = send_dt.hour
        weekday = send_dt.weekday()

        # 카테고리·타입·목적·세그먼트는 균등 샘플링
        category = _sample_enum(rng, Category)
        message_type = _sample_enum(rng, MessageType)
        purpose = _sample_enum(rng, CampaignPurpose)
        age = _sample_enum(rng, AgeGroup)
        region = _sample_enum(rng, Region)
        volume = int(rng.integers(MIN_VOLUME, MAX_VOLUME + 1))

        conv = _compute_conversion_rate(
            rng, category, hour, weekday, message_type, purpose, age, region
        )
        click_mult = float(rng.uniform(3.0, 5.0))
        open_mult = float(rng.uniform(5.0, 10.0))
        click = float(np.clip(conv * click_mult, 0.0, 1.0))
        open_rate = float(np.clip(click * open_mult, 0.0, 1.0))

        rows.append(
            {
                "campaign_id": str(uuid4()),
                "category": category.value,
                "send_datetime": send_dt,
                "hour": hour,
                "weekday": weekday,
                "message_type": message_type.value,
                "purpose": purpose.value,
                "target_age": age.value,
                "target_region": region.value,
                "volume": volume,
                "open_rate": open_rate,
                "click_rate": click,
                "conversion_rate": conv,
            }
        )

    return pd.DataFrame(rows)
