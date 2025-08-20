import pandas as pd
import streamlit as st

st.title("Ops KPI Dashboard — Demo")

# Load sample data
sales = pd.read_csv("data/sample_daily_sales.csv")

# Show key metric
st.metric("Daily Sales (Yesterday)", f"${int(sales['sales'].iloc[-1]):,}")

# Line chart of sales
st.line_chart(sales[['sales']].rename(columns={'sales':'Daily Sales'}))

st.write("Tip: Replace the CSV with your real daily report to see your own trends.")
