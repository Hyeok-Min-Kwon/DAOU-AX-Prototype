"""
도메인 가정 (Domain Assumptions)
================================

실제 비즈뿌리오 운영 데이터에 접근할 수 없으므로, 기업 메시지 캠페인의
일반적인 응답 패턴에 대한 가정을 코드로 명시한다. 모든 가정은 명시적이고
교체 가능하도록 모듈 레벨 상수로 둔다.

핵심 가정
---------
1. **시간대 효과**: 업종별로 수신자가 메시지에 반응하는 피크 시간대가 다르다.
   (외식업 → 점심·저녁 직전 / 금융 → 평일 오전 / 이커머스 → 저녁 휴식)
2. **요일 효과**: B2C는 주말, B2B/공공/금융은 평일(특히 화·수·목)이 강하다.
3. **메시지 타입 효과**: SMS < LMS < MMS < RCS 순으로 베이스라인 전환율이 높지만,
   업종에 따라 효과 폭이 다르다 (외식·이커머스는 이미지 효과 큼).
4. **캠페인 목적 효과**: 리텐션 > 알림 > 프로모션 > 휴면고객 재활성화 순.
5. **세그먼트 효과**: 연령대·지역에 따라 응답률이 다르다.
"""

from enum import Enum


# =========================
# 카테고리 정의
# =========================


class Category(str, Enum):
    FOOD_SERVICE = "food_service"
    FINANCE = "finance"
    ECOMMERCE = "ecommerce"
    BEAUTY = "beauty"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    TRAVEL = "travel"
    PUBLIC = "public"


class MessageType(str, Enum):
    SMS = "SMS"
    LMS = "LMS"
    MMS = "MMS"
    RCS = "RCS"


class CampaignPurpose(str, Enum):
    PROMOTION = "promotion"
    NOTIFICATION = "notification"
    RETENTION = "retention"
    REACTIVATION = "reactivation"


class AgeGroup(str, Enum):
    AGE_20S = "20s"
    AGE_30S = "30s"
    AGE_40S = "40s"
    AGE_50_PLUS = "50+"


class Region(str, Enum):
    METRO = "metro"
    NON_METRO = "non_metro"


# =========================
# 시간대 가중치 (24시간, 1.0이 평균)
# =========================
# 사람이 메시지를 열어보고 행동할 확률이 시간대별로 다르다고 가정.
# 외식업은 점심(11~12)·저녁(17~19) 직전에 의사결정이 일어남.
# 금융은 평일 오전 업무시간(9~11)에 집중.
# 이커머스·뷰티는 저녁 휴식시간(20~22)에 강함.
HOUR_WEIGHTS_BY_CATEGORY: dict[Category, list[float]] = {
    # fmt: off
    #                   0    1    2    3    4    5    6    7    8    9   10   11   12   13   14   15   16   17   18   19   20   21   22   23
    Category.FOOD_SERVICE: [0.2,0.1,0.1,0.1,0.1,0.2,0.4,0.6,0.8,0.9,1.0,1.6,1.5,0.9,0.8,0.8,0.9,1.6,1.7,1.3,1.0,0.8,0.6,0.4],
    Category.FINANCE:      [0.1,0.1,0.1,0.1,0.1,0.2,0.4,0.7,1.1,1.5,1.6,1.3,1.0,1.1,1.4,1.3,1.2,1.0,0.8,0.6,0.5,0.4,0.3,0.2],
    Category.ECOMMERCE:    [0.3,0.2,0.2,0.1,0.1,0.2,0.4,0.6,0.8,0.9,1.0,1.1,1.0,1.0,1.0,1.0,1.1,1.2,1.3,1.4,1.6,1.7,1.5,0.9],
    Category.BEAUTY:       [0.2,0.2,0.1,0.1,0.1,0.2,0.3,0.5,0.7,0.9,1.0,1.0,1.0,1.2,1.4,1.4,1.3,1.2,1.2,1.5,1.6,1.5,1.2,0.7],
    Category.EDUCATION:    [0.2,0.1,0.1,0.1,0.1,0.2,0.4,0.6,0.7,0.8,0.9,0.9,1.0,1.0,1.0,1.0,1.0,1.1,1.3,1.5,1.7,1.8,1.5,0.9],
    Category.HEALTHCARE:   [0.1,0.1,0.1,0.1,0.1,0.2,0.4,0.7,1.0,1.5,1.6,1.3,1.0,1.2,1.5,1.5,1.4,1.2,0.9,0.7,0.5,0.4,0.3,0.2],
    Category.TRAVEL:       [0.2,0.2,0.1,0.1,0.1,0.2,0.3,0.5,0.7,0.9,1.0,1.1,1.3,1.4,1.2,1.1,1.1,1.2,1.3,1.5,1.6,1.5,1.2,0.7],
    Category.PUBLIC:       [0.1,0.1,0.1,0.1,0.1,0.1,0.3,0.6,1.2,1.7,1.7,1.5,1.0,1.2,1.4,1.3,1.1,0.9,0.6,0.4,0.3,0.2,0.2,0.1],
    # fmt: on
}


# =========================
# 요일 가중치 (월=0 ~ 일=6, 1.0이 평균)
# =========================
# B2C(외식·이커머스·뷰티·여행)는 주말 강함.
# 금융·공공·교육은 화·수·목 평일 코어 강함, 월요일·금요일 저녁 약함.
WEEKDAY_WEIGHTS_BY_CATEGORY: dict[Category, list[float]] = {
    #                          월   화   수   목   금   토   일
    Category.FOOD_SERVICE: [0.9, 1.0, 1.0, 1.0, 1.2, 1.3, 1.2],
    Category.FINANCE:      [0.8, 1.2, 1.3, 1.2, 1.0, 0.7, 0.6],
    Category.ECOMMERCE:    [0.9, 1.0, 1.0, 1.0, 1.1, 1.3, 1.3],
    Category.BEAUTY:       [0.9, 1.0, 1.0, 1.0, 1.2, 1.4, 1.2],
    Category.EDUCATION:    [0.9, 1.1, 1.2, 1.2, 1.0, 0.9, 1.3],
    Category.HEALTHCARE:   [1.0, 1.2, 1.2, 1.2, 1.0, 0.8, 0.6],
    Category.TRAVEL:       [0.8, 0.9, 1.0, 1.1, 1.3, 1.4, 1.1],
    Category.PUBLIC:       [0.9, 1.2, 1.3, 1.2, 1.0, 0.7, 0.5],
}


# =========================
# 메시지 타입 베이스라인 전환율
# =========================
# 일반적으로 SMS는 1% 안팎, RCS는 3-4% 수준 (업계 추정치 기반).
TYPE_BASE_CONVERSION_RATE: dict[MessageType, float] = {
    MessageType.SMS: 0.010,
    MessageType.LMS: 0.015,
    MessageType.MMS: 0.022,
    MessageType.RCS: 0.032,
}


# =========================
# 업종 × 메시지 타입 상성 (1.0 = 효과 없음)
# =========================
# 음식·상품 등 시각 자극이 의사결정에 큰 영향을 주는 업종은
# 이미지·리치 컨텐츠(MMS/RCS) 효과가 크다.
CATEGORY_TYPE_BOOST: dict[Category, dict[MessageType, float]] = {
    Category.FOOD_SERVICE: {MessageType.MMS: 1.3, MessageType.RCS: 1.4},
    Category.ECOMMERCE:    {MessageType.MMS: 1.4, MessageType.RCS: 1.5},
    Category.BEAUTY:       {MessageType.MMS: 1.3, MessageType.RCS: 1.4},
    Category.TRAVEL:       {MessageType.MMS: 1.2, MessageType.RCS: 1.3},
    # 텍스트 위주 업종은 boost 없음
    Category.FINANCE:    {MessageType.SMS: 1.1, MessageType.LMS: 1.1},
    Category.PUBLIC:     {MessageType.SMS: 1.1, MessageType.LMS: 1.1},
    Category.HEALTHCARE: {MessageType.LMS: 1.1},
    Category.EDUCATION:  {MessageType.LMS: 1.1, MessageType.MMS: 1.1},
}


# =========================
# 캠페인 목적 멀티플라이어
# =========================
# 기존 고객 대상 리텐션은 효과가 가장 크고, 휴면 고객 재활성화는 어렵다.
PURPOSE_MULTIPLIER: dict[CampaignPurpose, float] = {
    CampaignPurpose.PROMOTION: 1.0,
    CampaignPurpose.NOTIFICATION: 1.2,
    CampaignPurpose.RETENTION: 1.5,
    CampaignPurpose.REACTIVATION: 0.6,
}


# =========================
# 세그먼트 멀티플라이어
# =========================
# 연령대별 디지털 친숙도·메시지 응답률 차이.
AGE_MULTIPLIER: dict[AgeGroup, float] = {
    AgeGroup.AGE_20S: 1.10,
    AgeGroup.AGE_30S: 1.05,
    AgeGroup.AGE_40S: 0.95,
    AgeGroup.AGE_50_PLUS: 0.85,
}

# 50대+ 는 RCS·MMS 효과가 상대적으로 약함 (텍스트 선호).
AGE_TYPE_MULTIPLIER: dict[AgeGroup, dict[MessageType, float]] = {
    AgeGroup.AGE_50_PLUS: {MessageType.MMS: 0.85, MessageType.RCS: 0.75},
    AgeGroup.AGE_40S:     {MessageType.RCS: 0.95},
}

REGION_MULTIPLIER: dict[Region, float] = {
    Region.METRO: 1.05,
    Region.NON_METRO: 0.95,
}


# =========================
# 노이즈 파라미터
# =========================
# 동일 조건이라도 캠페인별 자연 변동 (가우시안 noise).
CONVERSION_RATE_NOISE_STD = 0.15  # 전환율의 15% 표준편차

# 발송량이 작을수록 변동이 큼 (대수의 법칙) — 시뮬레이션에 반영.
MIN_VOLUME = 1_000
MAX_VOLUME = 500_000
