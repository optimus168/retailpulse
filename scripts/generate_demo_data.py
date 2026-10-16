"""Generate the clearly synthetic 500-row RetailPulse demo dataset."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

SEED = 20261016


def generate_demo_data(rows: int = 500, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    products = {
        "Cheese": ("Dairy", 135.0, 0.11),
        "Milk": ("Dairy", 58.0, 0.08),
        "Yogurt": ("Dairy", 72.0, 0.05),
        "Juice": ("Beverages", 92.0, 0.09),
        "Coffee": ("Beverages", 124.0, 0.08),
        "Tea": ("Beverages", 82.0, 0.07),
        "Bottled Water": ("Beverages", 25.0, 0.07),
        "Soda": ("Beverages", 48.0, 0.08),
        "Biscuits": ("Snacks", 31.0, 0.06),
        "Chips": ("Snacks", 35.0, 0.06),
        "Apples": ("Fruits", 112.0, 0.05),
        "Bananas": ("Fruits", 42.0, 0.04),
        "Potatoes": ("Vegetables", 34.0, 0.04),
        "Tomatoes": ("Vegetables", 39.0, 0.04),
        "Bread": ("Bakery", 46.0, 0.04),
        "Shampoo": ("Personal Care", 185.0, 0.04),
    }
    names = list(products)
    weights = np.array([products[p][2] for p in names], dtype=float)
    weights /= weights.sum()
    # Slightly elevated traffic and basket values at Branch C make the sample useful
    # for practice while avoiding any claim that these are the official workbook rows.
    branches = ["A - Jaipur", "B - Delhi", "C - Mumbai", "D - Bengaluru"]
    branch_weights = [0.22, 0.23, 0.32, 0.23]
    dates = pd.date_range("2026-03-01", "2026-06-30", freq="D")
    date_weights = np.array([1.0 + 0.20 * np.sin(i / 7) + (0.2 if d.dayofweek in (5, 6) else 0) for i, d in enumerate(dates)])
    date_weights = date_weights / date_weights.sum()

    chosen_products = rng.choice(names, size=rows, p=weights)
    branch_choices = rng.choice(branches, size=rows, p=branch_weights)
    customer_types = rng.choice(["Member", "Normal"], size=rows, p=[0.48, 0.52])
    payment_methods = rng.choice(["UPI", "Cash", "Card", "Net Banking", "E-wallet"], size=rows, p=[0.32, 0.24, 0.22, 0.13, 0.09])
    chosen_dates = rng.choice(dates.to_numpy(), size=rows, p=date_weights)

    records = []
    for i in range(rows):
        product = str(chosen_products[i])
        category, base_price, _ = products[product]
        branch = str(branch_choices[i])
        customer_type = str(customer_types[i])
        branch_factor = 1.13 if branch == "C - Mumbai" else 1.0
        price_noise = rng.uniform(0.90, 1.12)
        unit_price = round(base_price * price_noise, 2)
        max_quantity = 5 if customer_type == "Member" else 7
        quantity = int(rng.integers(1, max_quantity + 1))
        if branch == "C - Mumbai" and rng.random() < 0.35:
            quantity = min(max_quantity, quantity + 1)
        rating = round(float(np.clip(rng.normal(4.0 if branch != "D - Bengaluru" else 3.9, 0.52), 1.0, 5.0)), 1)
        records.append({
            "Invoice_ID": f"INV{i + 1:04d}",
            "Date": pd.Timestamp(chosen_dates[i]).strftime("%Y-%m-%d"),
            "Branch": branch,
            "Customer_Type": customer_type,
            "Product": product,
            "Product_Category": category,
            "Quantity": quantity,
            "Unit_Price": round(unit_price * branch_factor, 2),
            "Payment_Method": str(payment_methods[i]),
            "Rating": rating,
        })
    return pd.DataFrame(records)


if __name__ == "__main__":
    output = Path(__file__).resolve().parents[1] / "data" / "supermarket_sales.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    generate_demo_data().to_csv(output, index=False)
    print(f"Created {output} with 500 synthetic transactions")
