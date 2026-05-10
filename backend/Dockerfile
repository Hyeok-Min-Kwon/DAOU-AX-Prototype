FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/backend

# 시스템 런타임 의존성 (LightGBM/XGBoost가 요구하는 OpenMP)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# uv 바이너리 (이미지에서 직접 복사 — 빠르고 캐시 친화적)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 의존성 명세만 먼저 복사 → 레이어 캐시 활용
COPY pyproject.toml ./
RUN uv sync --no-install-project

# 애플리케이션 코드는 docker-compose에서 볼륨 마운트로 주입 (개발 편의)
EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--app-dir", "backend"]
