from __future__ import annotations

import random
from pathlib import Path

import pandas as pd


def generate_sample_sales(path: str | Path, rows: int = 300) -> None:
    random.seed(42)

    regions = ["North", "South", "East", "West"]
    products = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]

    start_date = pd.Timestamp("2023-01-01")
    dates = [start_date + pd.Timedelta(days=i) for i in range(rows)]

    data = []
    for idx, date in enumerate(dates):
        region = regions[idx % len(regions)]
        product = products[idx % len(products)]
        units_sold = random.randint(10, 120)
        base_price = {"Alpha": 50, "Beta": 70, "Gamma": 40, "Delta": 90, "Epsilon": 60}[product]
        seasonal_multiplier = 1.0 + (date.month % 3) * 0.05
        revenue = round(units_sold * base_price * seasonal_multiplier, 2)
        quarter = f"Q{((date.month - 1) // 3) + 1}"

        data.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "region": region,
                "product": product,
                "units_sold": units_sold,
                "revenue": revenue,
                "quarter": quarter,
            }
        )

    df = pd.DataFrame(data)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


if __name__ == "__main__":
    generate_sample_sales("data/sample_sales.csv", rows=300)
