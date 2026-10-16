"""Data preparation and transparent business analytics for RetailPulse."""
from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "Invoice_ID", "Date", "Branch", "Product", "Product_Category",
    "Quantity", "Unit_Price", "Customer_Type", "Payment_Method", "Rating",
]
CORE_COLUMNS = ["Invoice_ID", "Date", "Branch", "Product", "Product_Category", "Quantity", "Unit_Price"]

ALIASES = {
    "Invoice_ID": {"invoice id", "invoice_id", "invoice", "order id", "order_id", "transaction id", "transaction_id", "bill id"},
    "Date": {"date", "order date", "order_date", "transaction date", "transaction_date"},
    "Branch": {"branch", "store", "store branch", "location"},
    "Product": {"product", "item", "product name", "sku"},
    "Product_Category": {"product category", "product_category", "product line", "product_line", "category"},
    "Quantity": {"quantity", "qty", "units", "unit count"},
    "Unit_Price": {"unit price", "unit_price", "price per unit", "price", "unit cost"},
    "Customer_Type": {"customer type", "customer_type", "customer segment", "segment", "membership"},
    "Payment_Method": {"payment", "payment method", "payment_method", "payment type", "payment_type"},
    "Rating": {"rating", "customer rating", "customer_rating", "satisfaction rating"},
}


def _key(value: Any) -> str:
    """Normalize a heading for alias matching."""
    return re.sub(r"\s+", " ", re.sub(r"[_\-]+", " ", str(value).strip().lower()))


def _money_number(series: pd.Series) -> pd.Series:
    """Parse numbers that may contain currency signs or comma separators."""
    cleaned = series.astype("string").str.replace(r"[^0-9.\-]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def standardize_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Map common supermarket CSV headings to the project's canonical schema."""
    frame = data.copy()
    normalized_aliases: dict[str, str] = {}
    for canonical, options in ALIASES.items():
        for option in options | {canonical.lower(), canonical.lower().replace("_", " ")}:
            normalized_aliases[_key(option)] = canonical
    rename = {}
    for col in frame.columns:
        match = normalized_aliases.get(_key(col))
        if match and match not in rename.values():
            rename[col] = match
    frame = frame.rename(columns=rename)
    return frame


def prepare_dataset(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Return (clean data, normalized source data, quality audit).

    Sales are calculated as Quantity * Unit_Price as specified in the class capstone.
    Invalid dates, non-positive quantities/prices, blank invoice IDs, and duplicate
    invoice IDs are excluded from the analysis view, but counts remain visible in
    the data-quality audit. The input frame is not mutated.
    """
    if raw is None or raw.empty:
        raise ValueError("The uploaded file contains no rows.")

    frame = standardize_columns(raw)
    missing_core = [col for col in CORE_COLUMNS if col not in frame.columns]
    if missing_core:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing_core) +
            ". Required fields are invoice ID, date, branch, product, product category, quantity, and unit price."
        )

    # Add optional fields so datasets with differing schemas can still be analyzed.
    for optional, default in [("Customer_Type", "Unknown"), ("Payment_Method", "Unknown"), ("Rating", np.nan)]:
        if optional not in frame.columns:
            frame[optional] = default

    frame = frame[REQUIRED_COLUMNS].copy()
    source_row_count = len(frame)

    # Audit counts are computed before filtering/cleaning.
    missing_by_column = frame.isna().sum().to_dict()
    for col in frame.select_dtypes(include=["object", "string"]).columns:
        missing_by_column[col] = int(missing_by_column.get(col, 0) + frame[col].astype("string").str.strip().eq("").sum())

    original_invoice = frame["Invoice_ID"].astype("string").str.strip()
    duplicate_invoice_rows = int(original_invoice.duplicated(keep="first").sum())
    exact_duplicate_rows = int(frame.duplicated().sum())

    frame["Invoice_ID"] = original_invoice
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce", format="mixed", dayfirst=True)
    frame["Quantity"] = _money_number(frame["Quantity"])
    frame["Unit_Price"] = _money_number(frame["Unit_Price"])
    frame["Rating"] = _money_number(frame["Rating"])

    invalid_dates = int(frame["Date"].isna().sum())
    invalid_quantity = int((frame["Quantity"].isna() | (frame["Quantity"] <= 0)).sum())
    invalid_price = int((frame["Unit_Price"].isna() | (frame["Unit_Price"] <= 0)).sum())
    missing_invoice = int(frame["Invoice_ID"].isna().sum() + frame["Invoice_ID"].astype("string").str.strip().eq("").sum())

    for col in ["Branch", "Product", "Product_Category", "Customer_Type", "Payment_Method"]:
        frame[col] = frame[col].astype("string").str.strip().replace("", pd.NA)
    missing_label_rows = int(frame[["Branch", "Product", "Product_Category"]].isna().any(axis=1).sum())

    clean = frame.dropna(subset=CORE_COLUMNS).copy()
    clean = clean[(clean["Quantity"] > 0) & (clean["Unit_Price"] > 0)]
    clean = clean[clean["Invoice_ID"].astype("string").str.strip().ne("")]
    clean = clean.drop_duplicates(subset=["Invoice_ID"], keep="first")

    for col in ["Customer_Type", "Payment_Method"]:
        clean[col] = clean[col].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    for col in ["Branch", "Product", "Product_Category"]:
        clean[col] = clean[col].astype(str).str.strip()

    clean["Sales"] = clean["Quantity"] * clean["Unit_Price"]
    clean["Month"] = clean["Date"].dt.to_period("M").dt.to_timestamp()
    clean["Week"] = clean["Date"].dt.to_period("W").dt.start_time
    clean["Day"] = clean["Date"].dt.date

    # Keep the normalized frame available for the audit table without mutating input.
    audit = {
        "source_rows": source_row_count,
        "clean_rows": len(clean),
        "removed_rows": source_row_count - len(clean),
        "duplicate_invoice_rows": duplicate_invoice_rows,
        "exact_duplicate_rows": exact_duplicate_rows,
        "invalid_dates": invalid_dates,
        "invalid_quantities": invalid_quantity,
        "invalid_unit_prices": invalid_price,
        "missing_invoice_ids": missing_invoice,
        "rows_with_missing_labels": missing_label_rows,
        "missing_by_column": {str(k): int(v) for k, v in missing_by_column.items() if v > 0},
    }
    return clean.reset_index(drop=True), frame.reset_index(drop=True), audit


def currency(value: float | int) -> str:
    """Format Indian Rupee values using Indian digit grouping."""
    if pd.isna(value):
        value = 0
    return "₹" + format(float(value), ",.2f")


def build_recommendations(data: pd.DataFrame) -> list[dict[str, str]]:
    """Generate transparent, data-dependent business observations and actions."""
    if data.empty:
        return []
    recommendations: list[dict[str, str]] = []

    branch_sales = data.groupby("Branch", dropna=False)["Sales"].sum().sort_values(ascending=False)
    product_sales = data.groupby("Product", dropna=False)["Sales"].sum().sort_values(ascending=False)
    category_sales = data.groupby("Product_Category", dropna=False)["Sales"].sum().sort_values(ascending=False)
    payment_counts = data["Payment_Method"].value_counts(dropna=False)

    if not branch_sales.empty:
        recommendations.append({
            "title": "Branch performance",
            "observation": f"{branch_sales.index[0]} leads with {currency(branch_sales.iloc[0])} in sales.",
            "action": "Compare its product mix, stock availability and checkout operations with lower-performing branches before replicating practices.",
        })
    if not product_sales.empty:
        recommendations.append({
            "title": "Product priority",
            "observation": f"{product_sales.index[0]} is the highest-revenue product in the current selection ({currency(product_sales.iloc[0])}).",
            "action": "Review availability and replenishment for this item; validate margin and spoilage before increasing inventory.",
        })
    if not category_sales.empty:
        total = category_sales.sum()
        share = (category_sales.iloc[0] / total * 100) if total else 0
        recommendations.append({
            "title": "Category concentration",
            "observation": f"{category_sales.index[0]} contributes {share:.1f}% of sales in the selected data.",
            "action": "Protect availability in the leading category while testing targeted cross-category bundles to diversify sales.",
        })
    if not payment_counts.empty:
        share = payment_counts.iloc[0] / payment_counts.sum() * 100
        recommendations.append({
            "title": "Payment experience",
            "observation": f"{payment_counts.index[0]} is the most-used payment method ({share:.1f}% of transactions).",
            "action": "Keep this checkout option reliable and monitor payment failure rates and queue times across branches.",
        })

    if data["Customer_Type"].nunique() >= 2:
        mean_spend = data.groupby("Customer_Type")["Sales"].mean().sort_values(ascending=False)
        if len(mean_spend) >= 2:
            leader, laggard = mean_spend.index[0], mean_spend.index[-1]
            recommendations.append({
                "title": "Customer segment comparison",
                "observation": f"{leader} transactions average {currency(mean_spend.iloc[0])}, compared with {currency(mean_spend.iloc[-1])} for {laggard}.",
                "action": "Test a small, measurable loyalty offer and compare repeat visits and average basket value against a control group.",
            })
    return recommendations
