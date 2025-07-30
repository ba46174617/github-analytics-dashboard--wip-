import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

st.set_page_config(page_title="GitHub Analytics Dashboard", layout="wide")
data_dir = Path('.')

# Load preprocessed data
@st.cache_data
def load_data():
    return {
        "contributor_summary": pd.read_parquet(data_dir / "contributor_summary.parquet"),
        "monthly_commits": pd.read_parquet(data_dir / "monthly_commits.parquet"),
        "pr_summary": pd.read_parquet(data_dir / "pr_summary.parquet"),
        "issues_by_status": pd.read_parquet(data_dir / "issues_by_status.parquet"),
        "punch_summary": pd.read_parquet(data_dir / "punch_summary.parquet"),
    }

data = load_data()

# Sidebar filters
st.sidebar.title("Filters")
month_filter = st.sidebar.selectbox("Select Month", data["monthly_commits"]["month"].astype(str).unique())

# Layout
st.title("GitHub Analytics Dashboard")
st.markdown("### Contributor Metrics")
st.dataframe(data["contributor_summary"].sort_values("commits", ascending=False))

# Commits over time
st.markdown("### Monthly Commits by Author")
filtered_commits = data["monthly_commits"][data["monthly_commits"]["month"].astype(str) == month_filter]

commit_chart = alt.Chart(filtered_commits).mark_bar().encode(
    x=alt.X("author:N", sort="-y"),
    y="commit_count:Q",
    color="author:N",
    tooltip=["author", "commit_count"]
).properties(width=700, height=400)

st.altair_chart(commit_chart)

# Pull requests
st.markdown("### Pull Requests Summary")
st.dataframe(data["pr_summary"].sort_values("pull_requests", ascending=False))

# Issues
st.markdown("### Issues by Status")
st.dataframe(data["issues_by_status"].fillna(0).astype(int))

# Punch card
st.markdown("### Punch Card Activity")
punch = data["punch_summary"]
punch_chart = alt.Chart(punch).mark_circle(size=60).encode(
    x=alt.X("hour:O", title="Hour of Day"),
    y=alt.Y("weekday:O", title="Weekday"),
    size="commits:Q",
    color="commits:Q",
    tooltip=["weekday", "hour", "commits"]
).properties(width=700, height=400)

st.altair_chart(punch_chart)