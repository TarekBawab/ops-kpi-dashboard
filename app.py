import pandas as pd
import streamlit as st

# ================================
# Page setup + Global CSS (fonts)
# ================================
st.set_page_config(page_title="Ops KPI Dashboard", page_icon="📊", layout="wide")

# Force a consistent font and simple cards for metrics/stat boxes
st.markdown(
    """
    <style>
      html, body, [class*="block-container"] * {
        font-family: Arial, sans-serif !important;
      }
      .metric-box {
        padding: 12px 14px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        background: #f7f8fa;
        margin-bottom: 8px;
      }
      .metric-label {
        font-weight: 600;
        color: #374151;
        margin-bottom: 2px;
        font-size: 13px;
      }
      .metric-value {
        font-weight: 700;
        font-size: 22px;
        color: #111827;
        line-height: 1.2;
      }
      .good { color: #0a7d33; }   /* green */
      .bad  { color: #b00020; }   /* red   */
      .muted { color: #6b7280; font-size: 13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Ops KPI Dashboard — Demo")

# ================================
# Helpers
# ================================
@st.cache_data
def load_csv(file_like):
    """Read CSV and normalize columns. Expect columns: date,sales."""
    df = pd.read_csv(file_like)
    df.columns = [c.strip().lower() for c in df.columns]
    if "date" not in df.columns or "sales" not in df.columns:
        raise ValueError("CSV must have columns: date,sales")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df[["date", "sales"]]

def metric_card(label: str, value_html: str, extra_html: str = ""):
    """Render a consistent metric card with matching fonts."""
    st.markdown(
        f"""
        <div class="metric-box">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value_html}</div>
          {f'<div class="muted">{extra_html}</div>' if extra_html else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ================================
# Sidebar — Data source & Templates
# ================================
st.sidebar.header("Data")
uploaded = st.sidebar.file_uploader("Upload CSV (columns: date,sales)", type=["csv"])

st.sidebar.header("Templates")
with st.sidebar.expander("Download a CSV template"):
    template_kind = st.radio(
        "Template type", ["Daily (last 30 days)", "Monthly (last 12 months)"], index=0
    )
    include_examples = st.checkbox(
        "Include example values",
        value=True,
        help="If unchecked, 'sales' will be blank so you can fill it.",
    )

    # Build template dataframe
    if template_kind.startswith("Daily"):
        end = pd.Timestamp.today().normalize()
        dates = pd.date_range(end - pd.Timedelta(days=29), end, freq="D")
    else:
        end = pd.Timestamp.today().normalize().replace(day=1)
        dates = pd.date_range(end - pd.DateOffset(months=11), end, freq="MS")

    if include_examples:
        base = 3800 if template_kind.startswith("Daily") else 100000
        vals = [int(base * (1 + i / (len(dates) * 20))) for i in range(len(dates))]
        df_tmpl = pd.DataFrame({"date": dates.date, "sales": vals})
    else:
        df_tmpl = pd.DataFrame({"date": dates.date, "sales": [""] * len(dates)})

    st.download_button(
        label="⬇️ Download template CSV",
        data=df_tmpl.to_csv(index=False).encode("utf-8"),
        file_name="daily_template.csv" if template_kind.startswith("Daily") else "monthly_template.csv",
        mime="text/csv",
        help="Download, edit the Sales column, then upload it back above.",
    )

# Sidebar — View
view = st.sidebar.radio("View", ["Daily", "Monthly"], horizontal=True, index=0)

# ================================
# Load data (uploaded or sample)
# ================================
try:
    if uploaded:
        sales = load_csv(uploaded)
    else:
        sales = load_csv("data/sample_daily_sales.csv")
except Exception as e:
    st.error(f"Problem loading CSV: {e}")
    st.stop()

# Success summary (consistent fonts)
st.success(
    f"Loaded {len(sales)} rows from {sales['date'].min().date()} to {sales['date'].max().date()}"
)

total = int(sales["sales"].sum())
avg = int(sales["sales"].mean())

# Top metric row (consistent cards)
col1, col2 = st.columns([1, 1])
with col1:
    metric_card("Total Sales", f"${total:,}")
with col2:
    # "Most Recent" = last row of daily sales; for monthly view users still see daily most recent here
    latest_val = int(sales["sales"].iloc[-1])
    metric_card("Sales (Most Recent)", f"${latest_val:,}")

# ================================
# Apply view (daily / monthly)
# ================================
if view == "Monthly":
    sales_view = (
        sales.set_index("date")
        .resample("M")["sales"].sum()
        .rename_axis("date")
        .reset_index()
    )
else:
    sales_view = sales.copy()

# ================================
# Chart + export
# ================================
st.line_chart(sales_view.set_index("date")["sales"], use_container_width=True)

csv_view = sales_view.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download current view (CSV)",
    data=csv_view,
    file_name="sales_view.csv",
    mime="text/csv",
)

# ================================
# Best / Worst (consistent fonts & colors)
# ================================
best_row = sales_view.loc[sales_view["sales"].idxmax()]
worst_row = sales_view.loc[sales_view["sales"].idxmin()]

best_date = best_row["date"].date()
best_val = int(best_row["sales"])
worst_date = worst_row["date"].date()
worst_val = int(worst_row["sales"])

col3, col4 = st.columns([1, 1])
with col3:
    metric_card("Best", f"<span class='good'>{best_date} → ${best_val:,}</span>")
with col4:
    metric_card("Worst", f"<span class='bad'>{worst_date} → ${worst_val:,}</span>")

st.caption("Templates: Keep headers exactly `date,sales`. Dates can be daily or 1st of each month.")
