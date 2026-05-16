"""캠페인 합성 데이터 생성 CLI.

실행 예 (컨테이너):
    docker compose run --rm api python backend/scripts/generate_data.py
"""

import argparse
from datetime import datetime
from pathlib import Path

from src.data.generator import generate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic campaign dataset.")
    parser.add_argument("--n", type=int, default=50_000, help="row 개수")
    parser.add_argument("--out", type=Path, default=Path("data/campaigns.parquet"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--start", type=str, default="2025-01-01")
    parser.add_argument("--end", type=str, default="2025-12-31")
    args = parser.parse_args()

    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)

    print(f"Generating {args.n:,} campaigns from {start.date()} to {end.date()}...")
    df = generate_dataset(args.n, start, end, seed=args.seed)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out, index=False)
    size_kb = args.out.stat().st_size / 1024
    print(f"[OK] Parquet : {args.out}  ({len(df):,} rows, {size_kb:,.1f} KB)")

    sample_path = args.out.parent / "campaigns_sample.csv"
    df.head(1000).to_csv(sample_path, index=False)
    print(f"[OK] Sample  : {sample_path}  (1,000 rows)")

    print("\nNumeric column summary:")
    summary = df[["volume", "open_rate", "click_rate", "conversion_rate"]].describe()
    print(summary.round(4))


if __name__ == "__main__":
    main()
