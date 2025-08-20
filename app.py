import pandas as pd
import streamlit as st

st.set_page_config(page_title="Ops KPI Dashboard", page_icon="📊", layout="wide")
st.title("Ops KPI Dashboard — Demo")

# ---- Data loader ----
@st.cache_data
def load_csv(file):
    df = pd.read_csv(file)
    # normalize column names
    df.columns = [c.strip().lower() for c in df.columns]
    # expect date,sales
    if "date" not in df.columns or "sales" not in df.columns:
        raise ValueError("CSV must have columns: date,sales")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df[["date", "sales"]]

# Sidebar controls
st.sidebar.header("Data")
uploaded = st.sidebar.file_uploader("Upload CSV (columns: date,sales)", type=["csv"])
view = st.sidebar.radio("View", ["Daily", "Monthly"], horizontal=True)

# --- Template CSV downloader (daily / monthly) ---
st.sidebar.header("Templates")
with st.sidebar.expander("Download a CSV template"):
    template_kind = st.radio(
        "Template type",
        ["Daily (last 30 days)", "Monthly (last 12 months)"],
        horizontal=False,
    )
    include_examples = st.checkbox("Include example values", value=True,
                                   help="If unchecked, 'sales' will be blank so you can fill it.")

    import datetime as dt

    if template_kind.startswith("Daily"):
        # last 30 days
        end = pd.Timestamp.today().normalize()
        dates = pd.date_range(end - pd.Timedelta(days=29), end, freq="D")
    else:
        # last 12 months, first day of each month
        end = pd.Timestamp.today().normalize().replace(day=1)
        dates = pd.date_range(end - pd.DateOffset(months=11), end, freq="MS")

    if include_examples:
        # simple example values (feel free to change the pattern)
        # daily: gentle upward trend; monthly: bigger numbers
        base = 3800 if template_kind.startswith("Daily") else 100000
        vals = [int(base * (1 + i / (len(dates) * 20))) for i in range(len(dates))]
        df_tmpl = pd.DataFrame({"date": dates.date, "sales": vals})
    else:
        df_tmpl = pd.DataFrame({"date": dates.date, "sales": [""] * len(dates)})

    csv_bytes = df_tmpl.to_csv(index=False).encode("utf-8")
    fname = "daily_template.csv" if template_kind.startswith("Daily") else "monthly_template.csv"

    st.download_button(
        label="⬇️ Download template CSV",
        data=csv_bytes,
        file_name=fname,
        mime="text/csv",
        help="Download, edit the Sales column, then upload it back above."
    )


# Default to bundled sample if no upload
if uploaded:
    sales = load_csv(uploaded)
else:
    sales = load_csv("data/sample_daily_sales.csv")

# Aggregate if monthly view
if view == "Monthly":
    sales_view = (sales
                  .set_index("date")
                  .resample("M")["sales"].sum()
                  .rename_axis("date")
                  .reset_index())
else:
    sales_view = sales.copy()

# KPIs
latest = sales["sales"].iloc[-1]
st.metric("Sales (Most Recent)", f"${int(latest):,}")

# Chart
st.line_chart(sales_view.set_index("date")["sales"], use_container_width=True)

st.caption("Templates: Keep headers exactly `date,sales`. Dates can be daily or 1st of each month. Edit, save, and re‑upload in the sidebar.")

