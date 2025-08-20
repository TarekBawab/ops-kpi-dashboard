import pandas as pd
import streamlit as st

# ---- Page config ----
st.set_page_config(page_title="Ops KPI Dashboard", page_icon="📊", layout="wide")
st.title("Ops KPI Dashboard — Demo")

# ---- Helpers ----
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

# ---- Sidebar: data source ----
st.sidebar.header("Data")
uploaded = st.sidebar.file_uploader("Upload CSV (columns: date,sales)", type=["csv"])

# ---- Sidebar: templates to download ----
st.sidebar.header("Templates")
with st.sidebar.expander("Download a CSV template"):
    template_kind = st.radio(
        "Template type",
        ["Daily (last 30 days)", "Monthly (last 12 months)"],
        index=0
    )
    include_examples = st.checkbox(
        "Include example values",
        value=True,
        help="If unchecked, 'sales' will be blank so you can fill it."
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
        help="Download, edit the Sales column, then upload it back above."
    )

# ---- Sidebar: view options ----
view = st.sidebar.radio("View", ["Daily", "Monthly"], horizontal=True, index=0)

# ---- Load data (uploaded or sample) ----
try:
    if uploaded:
        sales = load_csv(uploaded)
    else:
        # Fallback to bundled sample
        sales = load_csv("data/sample_daily_sales.csv")
except Exception as e:
    st.error(f"Problem loading CSV: {e}")
    st.stop()

# ✅ Success message + quick summary
st.success(
    f"Loaded {len(sales)} rows "
    f"from {sales['date'].min().date()} to {sales['date'].max().date()}"
)
total = int(sales["sales"].sum())
avg = int(sales["sales"].mean())
st.write(f"**Total sales:** ${total:,} · **Average:** ${avg:,}")

# ---- Apply view (daily / monthly) ----
if view == "Monthly":
    sales_view = (
        sales.set_index("date")
        .resample("M")["sales"].sum()
        .rename_axis("date")
        .reset_index()
    )
else:
    sales_view = sales.copy()

# ---- KPIs ----
latest_val = int(sales["sales"].iloc[-1])
st.metric("Sales (Most Recent)", f"${latest_val:,}")

# ---- Chart ----
st.line_chart(sales_view.set_index("date")["sales"], use_container_width=True)

# ---- Download current view ----
csv_view = sales_view.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download current view (CSV)",
    data=csv_view,
    file_name="sales_view.csv",
    mime="text/csv"
)

# ---- Quick stats: best and worst period in current view ----
best = sales_view.loc[sales_view["sales"].idxmax()]
worst = sales_view.loc[sales_view["sales"].idxmin()]
st.write(
    f"**Best:** {best['date'].date()} → ${int(best['sales']):,} · "
    f"**Worst:** {worst['date'].date()} → ${int(worst['sales']):,}"
)

st.caption("Templates: Keep headers exactly `date,sales`. Dates can be daily or 1st of each month.")
