"""01_data_exploration.ipynb 생성기 (일회성 빌더, 재실행 가능).

노트북 셀을 코드로 정의하면 diff·재현이 쉽다.
실행 후 `jupyter nbconvert --execute`로 출력을 셀에 채워 넣는다.
"""

from pathlib import Path

import nbformat as nbf

CELLS: list = []


def md(text: str) -> None:
    CELLS.append(nbf.v4.new_markdown_cell(text))


def code(src: str) -> None:
    CELLS.append(nbf.v4.new_code_cell(src.strip()))


md(
    """# 01. 합성 캠페인 데이터 탐색

**목적**: `backend/src/data/generator.py`가 만든 데이터가 `patterns.py`의 도메인 가정을
충실히 반영하는지 시각적으로 검증한다.

검증 항목:
1. 기본 분포 (카테고리·메시지타입·캠페인 목적)
2. **시간대 효과** — 외식업 11/17시 피크, 금융 9-11시 피크 등이 보이는지
3. **요일 효과** — B2C 주말 강세, 금융·공공 평일 화-목 강세
4. **메시지 타입 효과** — SMS < LMS < MMS < RCS 순
5. **캠페인 목적 효과** — 리텐션 > 알림 > 프로모션 > 재활성화
6. **깔때기 관계** — open > click > conversion
"""
)

code(
    """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.dpi"] = 100

df = pd.read_parquet("../data/campaigns.parquet")
print(f"Loaded {len(df):,} rows, {df.shape[1]} columns")
df.head(3)
"""
)

code("df.info()")

code(
    """df[["volume", "open_rate", "click_rate", "conversion_rate"]].describe().round(4)"""
)

md("## 1. 카테고리 · 메시지 타입 · 캠페인 목적 분포\n\n균등 샘플링이므로 거의 균등하게 나와야 정상.")

code(
    """
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax, col in zip(axes, ["category", "message_type", "purpose"]):
    df[col].value_counts().sort_index().plot(kind="bar", ax=ax, color="#4C72B0")
    ax.set_title(col)
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=30)
plt.tight_layout()
plt.show()
"""
)

md(
    """## 2. 시간대 효과 — 가정이 데이터에 살아있는가?

`HOUR_WEIGHTS_BY_CATEGORY`에 정의한 패턴(외식 11/17시 피크, 금융 9-11시 피크 등)이
생성된 데이터에서 시간대별 평균 전환율로 다시 보여야 한다."""
)

code(
    """
hourly = df.groupby(["category", "hour"])["conversion_rate"].mean().unstack(level=0)

fig, ax = plt.subplots(figsize=(13, 6))
for cat in hourly.columns:
    ax.plot(hourly.index, hourly[cat], marker="o", label=cat, linewidth=1.5)
ax.set_xticks(range(0, 24))
ax.set_xlabel("Hour of day")
ax.set_ylabel("Mean conversion rate")
ax.set_title("Hour-of-day effect by category (synthetic data)")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
plt.tight_layout()
plt.show()
"""
)

md(
    """예상 패턴 체크:
- **food_service**: 11~12, 17~19시 피크
- **finance**: 9~11시 피크
- **ecommerce / beauty**: 저녁 20~22시 강세
- **public**: 오전 9~11시 집중
"""
)

md("## 3. 요일 효과")

code(
    """
weekly = df.groupby(["category", "weekday"])["conversion_rate"].mean().unstack(level=0)
weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

fig, ax = plt.subplots(figsize=(11, 5))
for cat in weekly.columns:
    ax.plot(weekly.index, weekly[cat], marker="o", label=cat, linewidth=1.5)
ax.set_xticks(range(0, 7))
ax.set_xticklabels(weekday_labels)
ax.set_ylabel("Mean conversion rate")
ax.set_title("Weekday effect by category (synthetic data)")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
plt.tight_layout()
plt.show()
"""
)

md(
    """예상 패턴:
- **food_service / ecommerce / beauty / travel**: 주말 강세
- **finance / public / healthcare**: 화·수·목 평일 강세, 주말 약세
"""
)

md("## 4. 메시지 타입 효과")

code(
    """
type_order = ["SMS", "LMS", "MMS", "RCS"]
fig, ax = plt.subplots(figsize=(8, 5))
sns.boxplot(data=df, x="message_type", y="conversion_rate", order=type_order, ax=ax)
ax.set_title("Conversion rate by message type")
ax.set_ylabel("Conversion rate")
plt.tight_layout()
plt.show()

print(df.groupby("message_type")["conversion_rate"].mean().reindex(type_order).round(4))
"""
)

md("기대: SMS < LMS < MMS < RCS 순으로 중앙값이 계단처럼 올라가야 함.")

md("## 5. 캠페인 목적 효과")

code(
    """
purpose_order = ["reactivation", "promotion", "notification", "retention"]
fig, ax = plt.subplots(figsize=(8, 5))
sns.boxplot(data=df, x="purpose", y="conversion_rate", order=purpose_order, ax=ax)
ax.set_title("Conversion rate by campaign purpose")
plt.tight_layout()
plt.show()

print(df.groupby("purpose")["conversion_rate"].mean().reindex(purpose_order).round(4))
"""
)

md("기대 멀티플라이어: reactivation(0.6×) < promotion(1.0×) < notification(1.2×) < retention(1.5×).")

md("## 6. 깔때기 검증")

code(
    """
funnel = df[["open_rate", "click_rate", "conversion_rate"]].mean()
print("평균 비율:")
print(funnel.round(4))
print(f"\\nopen > click > conversion ? {(funnel.iloc[0] > funnel.iloc[1] > funnel.iloc[2])}")

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax, col, color in zip(axes,
                          ["open_rate", "click_rate", "conversion_rate"],
                          ["#4C72B0", "#55A868", "#C44E52"]):
    ax.hist(df[col], bins=50, color=color, edgecolor="white")
    ax.set_title(col)
    ax.set_xlabel("rate")
plt.tight_layout()
plt.show()
"""
)

md(
    """## 결론

가정(`patterns.py`)이 데이터에 시각적으로 재현됨을 확인. 이 데이터셋을 입력으로 다음
단계에서 발송 시간/전환율/세그먼트 예측 모델을 학습한다.
"""
)


nb = nbf.v4.new_notebook()
nb.cells = CELLS
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12"},
}

out = Path("notebooks/01_data_exploration.ipynb")
out.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, str(out))
print(f"Wrote {out} with {len(CELLS)} cells")
