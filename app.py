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

st.caption("Tip: Upload your own CSV to see your numbers. Keep headers exactly: date,sales")
