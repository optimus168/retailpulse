"""RetailPulse — an interactive supermarket sales intelligence dashboard."""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.analytics import build_recommendations, currency, prepare_dataset  # noqa: E402

st.set_page_config(
    page_title="RetailPulse | Sales Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Compact, responsive styling: native Streamlit components remain accessible.
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
      html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
      .stApp { background: #f5f7fb; color: #17243b; }
      [data-testid="stSidebar"] { background: #101a30; }
      [data-testid="stSidebar"] * { color: #e9efff !important; }
      [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] { background: #182743; border-color: #3a4a68; }
      .hero { padding: 18px 22px; border-radius: 18px; background: linear-gradient(120deg,#152545,#234b7c 68%,#287e93); color: #fff; margin-bottom: 18px; }
      .hero h1 { font: 800 30px 'Manrope',sans-serif; margin: 0 0 5px 0; letter-spacing: -0.7px; color: #fff; }
      .hero p { margin: 0; color: #d4e6ff; font-size: 14px; }
      .eyebrow { text-transform: uppercase; letter-spacing: 1.5px; font-size: 10px; font-weight: 800; color: #75d5e7; margin-bottom: 6px; }
      .section-title { font: 800 18px 'Manrope',sans-serif; margin: 7px 0 12px; color: #192b49; }
      .metric-card { border: 1px solid #e5eaf3; background: #fff; border-radius: 15px; padding: 15px 16px; min-height: 99px; box-shadow: 0 4px 16px rgba(24,42,70,.035); }
      .metric-label { color: #71809a; font-size: 12px; font-weight: 600; margin-bottom: 6px; }
      .metric-value { font: 800 23px 'Manrope',sans-serif; color: #1c3152; letter-spacing: -.5px; }
      .metric-note { color: #8794a9; font-size: 11px; margin-top: 4px; }
      .insight-box { border: 1px solid #e3eaf3; background: #fff; border-radius: 14px; padding: 14px 15px; margin-bottom: 10px; }
      .insight-title { color: #1c3152; font-weight: 800; font-size: 13px; margin-bottom: 5px; }
      .insight-body { color: #52627c; font-size: 12px; line-height: 1.55; }
      .muted { color: #71809a; font-size: 12px; }
      div[data-testid="stMetric"] { background: white; border: 1px solid #e5eaf3; padding: 12px 14px; border-radius: 14px; }
      div[data-testid="stMetricLabel"] { color: #71809a; }
      div[data-testid="stMetricValue"] { color: #1c3152; font-family: 'Manrope',sans-serif; }
      .stTabs [data-baseweb="tab-list"] { gap: 8px; }
      .stTabs [data-baseweb="tab"] { background: #eaf0f8; border-radius: 10px 10px 0 0; padding: 8px 14px; }
      .stTabs [aria-selected="true"] { background: #fff !important; }
      @media (max-width: 720px) { .hero h1 { font-size: 24px; } .metric-value { font-size: 20px; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def money_metric(label: str, value: str, note: str) -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def chart_theme(fig, height: int = 330):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=18, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#52627c", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False, linecolor="#e8edf5", tickfont=dict(size=11))
    fig.update_yaxes(gridcolor="#edf1f7", zeroline=False, tickfont=dict(size=11))
    return fig


def safe_group_sum(data: pd.DataFrame, group: str) -> pd.DataFrame:
    return data.groupby(group, dropna=False, as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)


DEMO_PATH = ROOT / "data" / "supermarket_sales.csv"
with st.sidebar:
    st.markdown("<div class='eyebrow'>RETAIL INTELLIGENCE</div>", unsafe_allow_html=True)
    st.markdown("## RetailPulse")
    st.caption("Supermarket Sales · Decision Support")
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload your sales CSV", type=["csv"], help="Use the included demo data or upload a CSV with invoice, date, branch, product, category, quantity and unit price columns.")
    if uploaded_file is None:
        raw_data = pd.read_csv(DEMO_PATH)
        st.caption("Using the included synthetic demo dataset (500 rows).")
    else:
        try:
            raw_data = pd.read_csv(uploaded_file)
            st.caption(f"Uploaded: {uploaded_file.name}")
        except Exception as exc:
            st.error(f"Could not read the CSV: {exc}")
            st.stop()
    st.markdown("---")
    st.markdown("**Filters**")

try:
    data, normalized_source, quality = prepare_dataset(raw_data)
except Exception as exc:
    st.error(f"Dataset validation failed: {exc}")
    st.info("Download/export your file as CSV and check the required column names. Common names such as 'Invoice ID', 'Product line' and 'Unit price' are supported.")
    st.stop()

if data.empty:
    st.error("No valid transactions remain after data-quality checks. Review the Data Quality tab or upload a corrected file.")
    st.stop()

min_date = data["Date"].min().date()
max_date = data["Date"].max().date()
with st.sidebar:
    selected_dates = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    elif isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 1:
        start_date = end_date = selected_dates[0]
    else:
        start_date = end_date = selected_dates
    branch_options = sorted(data["Branch"].dropna().astype(str).unique().tolist())
    selected_branches = st.multiselect("Branch", branch_options, default=branch_options)
    category_options = sorted(data["Product_Category"].dropna().astype(str).unique().tolist())
    selected_categories = st.multiselect("Product category", category_options, default=category_options)
    customer_options = sorted(data["Customer_Type"].dropna().astype(str).unique().tolist())
    selected_customers = st.multiselect("Customer type", customer_options, default=customer_options)
    st.markdown("---")
    st.caption("All figures update from the current filters.")

filtered = data[
    data["Date"].dt.date.between(start_date, end_date)
    & data["Branch"].astype(str).isin(selected_branches)
    & data["Product_Category"].astype(str).isin(selected_categories)
    & data["Customer_Type"].astype(str).isin(selected_customers)
].copy()

st.markdown(
    "<div class='hero'><div class='eyebrow'>SUPERMARKET SALES ANALYTICS</div>"
    "<h1>Know your numbers. Make smarter moves.</h1>"
    "<p>Explore transaction trends, compare branches and products, and turn verified observations into practical actions.</p></div>",
    unsafe_allow_html=True,
)

if uploaded_file is None:
    st.caption("Demo data is synthetic and included for demonstration; replace it with the official course dataset before reporting real findings.")
else:
    st.caption(f"Analysis covers {start_date:%d %b %Y} – {end_date:%d %b %Y} · Data retained after validation: {len(data):,} rows")

if filtered.empty:
    st.warning("No transactions match the current filters. Widen the date range or select additional branches/categories.")
    st.stop()

sales_total = filtered["Sales"].sum()
transactions = len(filtered)
avg_order = filtered["Sales"].mean()
avg_rating = filtered["Rating"].mean()
with st.container():
    cols = st.columns(4, gap="medium")
    with cols[0]: money_metric("TOTAL SALES", currency(sales_total), "Quantity × unit price")
    with cols[1]: money_metric("TRANSACTIONS", f"{transactions:,}", f"{len(data):,} valid rows in dataset")
    with cols[2]: money_metric("AVG. BASKET VALUE", currency(avg_order), "Average sales per transaction")
    with cols[3]: money_metric("AVG. RATING", f"{avg_rating:.2f}/5" if pd.notna(avg_rating) else "N/A", "Average recorded customer rating")

st.markdown("<div class='section-title'>Sales performance overview</div>", unsafe_allow_html=True)
trend_col, branch_col = st.columns([1.45, 1], gap="large")
with trend_col:
    st.markdown("**Sales trend**")
    trend = filtered.set_index("Date").resample("W")["Sales"].sum().reset_index()
    if len(trend) <= 1:
        trend = filtered.groupby("Date", as_index=False)["Sales"].sum()
    fig = px.line(trend, x="Date", y="Sales", markers=True, color_discrete_sequence=["#198aa6"])
    fig.update_traces(line=dict(width=3), marker=dict(size=6), hovertemplate="%{x|%d %b %Y}<br>Sales: ₹%{y:,.2f}<extra></extra>")
    fig.update_layout(yaxis_title="Sales (₹)", xaxis_title="", hovermode="x unified")
    st.plotly_chart(chart_theme(fig, 330), use_container_width=True, config={"displayModeBar": False})
with branch_col:
    st.markdown("**Sales by branch**")
    branch_sales = safe_group_sum(filtered, "Branch")
    fig = px.bar(branch_sales, x="Sales", y="Branch", orientation="h", text="Sales", color="Sales", color_continuous_scale=["#d2edf2", "#177e97"])
    fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside", cliponaxis=False, hovertemplate="%{y}<br>Sales: ₹%{x:,.2f}<extra></extra>")
    fig.update_layout(xaxis_title="Sales (₹)", yaxis_title="", coloraxis_showscale=False, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(chart_theme(fig, 330), use_container_width=True, config={"displayModeBar": False})

# Main analysis workspaces.
tabs = st.tabs(["Product & Category", "Customers & Payments", "Decision Assistant", "Data Quality", "Explore Data"])
with tabs[0]:
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("**Revenue by product category**")
        category_sales = safe_group_sum(filtered, "Product_Category")
        fig = px.bar(category_sales.sort_values("Sales"), x="Sales", y="Product_Category", orientation="h", color_discrete_sequence=["#4d75b7"], text="Sales")
        fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside", cliponaxis=False)
        fig.update_layout(xaxis_title="Sales (₹)", yaxis_title="")
        st.plotly_chart(chart_theme(fig, 350), use_container_width=True, config={"displayModeBar": False})
    with right:
        st.markdown("**Top 10 products by sales**")
        product_sales = safe_group_sum(filtered, "Product").head(10).sort_values("Sales")
        fig = px.bar(product_sales, x="Sales", y="Product", orientation="h", color_discrete_sequence=["#1b9a8a"], text="Sales")
        fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside", cliponaxis=False)
        fig.update_layout(xaxis_title="Sales (₹)", yaxis_title="")
        st.plotly_chart(chart_theme(fig, 350), use_container_width=True, config={"displayModeBar": False})
    st.markdown("**Product performance table**")
    product_table = filtered.groupby(["Product", "Product_Category"], as_index=False).agg(
        Transactions=("Invoice_ID", "nunique"), Units_Sold=("Quantity", "sum"), Sales=("Sales", "sum"), Avg_Unit_Price=("Unit_Price", "mean")
    ).sort_values("Sales", ascending=False)
    st.dataframe(product_table.style.format({"Sales": "₹{:,.2f}", "Avg_Unit_Price": "₹{:,.2f}"}), use_container_width=True, hide_index=True)

with tabs[1]:
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("**Average basket value by customer type**")
        customer_sales = filtered.groupby("Customer_Type", as_index=False).agg(Average_Basket=("Sales", "mean"), Total_Sales=("Sales", "sum"), Transactions=("Invoice_ID", "nunique"))
        fig = px.bar(customer_sales, x="Customer_Type", y="Average_Basket", text="Average_Basket", color="Customer_Type", color_discrete_sequence=["#147d92", "#5c77bd", "#d29c46"])
        fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside", cliponaxis=False)
        fig.update_layout(xaxis_title="", yaxis_title="Average sales (₹)", showlegend=False)
        st.plotly_chart(chart_theme(fig, 315), use_container_width=True, config={"displayModeBar": False})
        st.dataframe(customer_sales.style.format({"Average_Basket": "₹{:,.2f}", "Total_Sales": "₹{:,.2f}"}), use_container_width=True, hide_index=True)
    with right:
        st.markdown("**Payment method mix**")
        payment_counts = filtered["Payment_Method"].value_counts().rename_axis("Payment_Method").reset_index(name="Transactions")
        fig = px.pie(payment_counts, names="Payment_Method", values="Transactions", hole=0.62, color_discrete_sequence=["#147d92", "#5c77bd", "#e3aa58", "#76b6aa", "#9a86c5"])
        fig.update_traces(textposition="outside", textinfo="label+percent", hovertemplate="%{label}<br>%{value} transactions (%{percent})<extra></extra>")
        fig.update_layout(showlegend=False)
        st.plotly_chart(chart_theme(fig, 315), use_container_width=True, config={"displayModeBar": False})
        st.markdown("**Customer rating distribution**")
        rating_data = filtered.dropna(subset=["Rating"])
        if rating_data.empty:
            st.info("No usable ratings in the selected rows.")
        else:
            fig = px.histogram(rating_data, x="Rating", nbins=9, color_discrete_sequence=["#1b9a8a"])
            fig.update_layout(xaxis_title="Rating (out of 5)", yaxis_title="Transactions", bargap=0.15)
            st.plotly_chart(chart_theme(fig, 245), use_container_width=True, config={"displayModeBar": False})

with tabs[2]:
    st.markdown("<div class='section-title'>Decision Assistant</div>", unsafe_allow_html=True)
    st.markdown("<p class='muted'>These are transparent, rule-based observations computed from the selected rows—not causal claims or model-generated predictions.</p>", unsafe_allow_html=True)
    recommendations = build_recommendations(filtered)
    rec_cols = st.columns(2, gap="medium")
    for idx, recommendation in enumerate(recommendations):
        with rec_cols[idx % 2]:
            st.markdown(
                f"<div class='insight-box'><div class='insight-title'>{recommendation['title']}</div>"
                f"<div class='insight-body'><b>Observation:</b> {recommendation['observation']}<br><br>"
                f"<b>Suggested action:</b> {recommendation['action']}</div></div>", unsafe_allow_html=True
            )
    st.info("Before acting, verify the pattern against the official dataset, profit margins, stock availability and operational context. Observed associations do not prove causation.")
    st.markdown("**Observation → Insight → Hypothesis → Recommendation**")
    st.write("Start with a measurable observation, interpret what it may mean, label unverified explanations as hypotheses, and then test a specific action.")

with tabs[3]:
    st.markdown("<div class='section-title'>Data quality audit</div>", unsafe_allow_html=True)
    st.write("The dashboard calculates sales from quantity × unit price. Data-quality counts below are computed before cleaning; excluded rows are not silently used in the charts.")
    qa_cols = st.columns(4)
    qa_cols[0].metric("Source rows", f"{quality['source_rows']:,}")
    qa_cols[1].metric("Valid rows", f"{quality['clean_rows']:,}")
    qa_cols[2].metric("Rows excluded", f"{quality['removed_rows']:,}")
    qa_cols[3].metric("Duplicate invoice rows", f"{quality['duplicate_invoice_rows']:,}")
    checks = pd.DataFrame([
        {"Check": "Invalid or unparseable dates", "Affected rows": quality["invalid_dates"], "Handling": "Excluded from analysis"},
        {"Check": "Missing/non-positive quantity", "Affected rows": quality["invalid_quantities"], "Handling": "Excluded from analysis"},
        {"Check": "Missing/non-positive unit price", "Affected rows": quality["invalid_unit_prices"], "Handling": "Excluded from analysis"},
        {"Check": "Missing invoice ID", "Affected rows": quality["missing_invoice_ids"], "Handling": "Excluded from analysis"},
        {"Check": "Rows with missing branch/product/category", "Affected rows": quality["rows_with_missing_labels"], "Handling": "Excluded from analysis"},
        {"Check": "Exact duplicate source rows", "Affected rows": quality["exact_duplicate_rows"], "Handling": "Invoice duplicates are deduplicated"},
    ])
    st.dataframe(checks, use_container_width=True, hide_index=True)
    st.markdown("**Missing values by source column**")
    missing = quality["missing_by_column"]
    if missing:
        missing_df = pd.DataFrame([{"Column": col, "Missing/blank values": count} for col, count in missing.items()]).sort_values("Missing/blank values", ascending=False)
        st.dataframe(missing_df, use_container_width=True, hide_index=True)
    else:
        st.success("No missing or blank values detected in the source columns.")
    if quality["removed_rows"] > 0:
        st.warning("Review excluded records before submitting results. The app intentionally avoids guessing corrections to invalid transactions.")
    else:
        st.success("All source rows passed the current validity checks.")

with tabs[4]:
    st.markdown("<div class='section-title'>Explore transactions</div>", unsafe_allow_html=True)
    search_text = st.text_input("Search invoice, branch, product or category", placeholder="e.g. INV0008, Mumbai, Cheese")
    table = filtered.copy()
    if search_text.strip():
        needle = search_text.strip().lower()
        mask = table[["Invoice_ID", "Branch", "Product", "Product_Category", "Customer_Type", "Payment_Method"]].astype(str).apply(lambda col: col.str.lower().str.contains(needle, regex=False)).any(axis=1)
        table = table[mask]
    display = table[["Invoice_ID", "Date", "Branch", "Customer_Type", "Product", "Product_Category", "Quantity", "Unit_Price", "Sales", "Payment_Method", "Rating"]].sort_values("Date", ascending=False)
    st.caption(f"Showing {len(display):,} rows after filters and search.")
    st.dataframe(display.style.format({"Unit_Price": "₹{:,.2f}", "Sales": "₹{:,.2f}", "Rating": "{:.1f}"}), use_container_width=True, hide_index=True)
    download = display.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered transactions (CSV)", data=download, file_name="retailpulse_filtered_sales.csv", mime="text/csv", use_container_width=False)

st.markdown("---")
foot_left, foot_right = st.columns([2, 1])
with foot_left:
    st.caption("RetailPulse · Academic project prototype · Synthetic demo data unless a real dataset is uploaded")
with foot_right:
    st.caption("Method: data audit → metric engineering → aggregation → visualization → recommendations")
