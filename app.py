import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# --------------------------------------------------
# Page Setup
# --------------------------------------------------
st.set_page_config(
    page_title="DATA 6999 Restaurant Risk Dashboard",
    page_icon="🍽️",
    layout="wide"
)

# --------------------------------------------------
# Load Data
# --------------------------------------------------
@st.cache_data
def load_data():
    dashboard_path = Path("data/processed/capstone_dashboard_dataset.csv")
    dennys_path = Path("data/processed/dennys_dashboard_validation.csv")

    dashboard_df = pd.read_csv(dashboard_path)

    if dennys_path.exists():
        dennys_df = pd.read_csv(dennys_path)
    else:
        dennys_df = pd.DataFrame()

    return dashboard_df, dennys_df


dashboard_df, dennys_df = load_data()

# --------------------------------------------------
# Basic Data Safety
# --------------------------------------------------
required_cols = ["state", "stars", "review_count"]

missing_required_cols = [
    col for col in required_cols
    if col not in dashboard_df.columns
]

if missing_required_cols:
    st.error(f"Missing required dashboard columns: {missing_required_cols}")
    st.stop()

# Clean basic fields
dashboard_df["state"] = dashboard_df["state"].astype(str).str.upper().str.strip()

if "city" in dashboard_df.columns:
    dashboard_df["city"] = dashboard_df["city"].astype(str).str.title().str.strip()

if "name" in dashboard_df.columns:
    dashboard_df["name"] = dashboard_df["name"].astype(str).str.strip()

# Make core numeric columns numeric
for col in ["stars", "review_count", "latitude", "longitude", "basic_risk_score", "low_rating_flag", "opportunity_flag", "is_open"]:
    if col in dashboard_df.columns:
        dashboard_df[col] = pd.to_numeric(dashboard_df[col], errors="coerce")

# If dashboard_risk_level was not saved, create it here
if "dashboard_risk_level" not in dashboard_df.columns:
    def assign_dashboard_risk_level(row):
        if row.get("is_open", 1) == 0:
            return "Closed / Inactive"
        elif row.get("low_rating_flag", 0) == 1:
            return "High Risk"
        elif row.get("basic_risk_score", 0) >= 2:
            return "Medium Risk"
        else:
            return "Low Risk"

    dashboard_df["dashboard_risk_level"] = dashboard_df.apply(assign_dashboard_risk_level, axis=1)

# --------------------------------------------------
# Dashboard Title
# --------------------------------------------------
st.title("DATA 6999 Capstone Dashboard")
st.subheader("Restaurant Performance Risk and Opportunity Model")

st.markdown(
    """
    This dashboard analyzes public restaurant performance signals to identify restaurants with potential
    operational risk or opportunity. It uses rating, review volume, market comparison, category indicators,
    and engineered risk flags to support restaurant-level and market-level decision-making.
    """
)

st.info(
    """
    **Business Use Case:** This dashboard helps identify restaurant locations that may need operational support
    based on public rating, review volume, market comparison, and engineered risk indicators.

    **Dashboard Objective:** Prioritize restaurants by risk level, compare performance across markets, and support
    a scalable restaurant risk-monitoring framework for the final DATA 6999 capstone project.
    """
)

# --------------------------------------------------
# Sidebar Filters
# --------------------------------------------------
st.sidebar.header("Dashboard Filters")

selected_states = st.sidebar.multiselect(
    "Select State(s)",
    options=sorted(dashboard_df["state"].dropna().unique()),
    default=sorted(dashboard_df["state"].dropna().unique())
)

selected_risk_levels = st.sidebar.multiselect(
    "Select Risk Level(s)",
    options=sorted(dashboard_df["dashboard_risk_level"].dropna().unique()),
    default=sorted(dashboard_df["dashboard_risk_level"].dropna().unique())
)

rating_range = st.sidebar.slider(
    "Rating Range",
    min_value=float(dashboard_df["stars"].min()),
    max_value=float(dashboard_df["stars"].max()),
    value=(float(dashboard_df["stars"].min()), float(dashboard_df["stars"].max())),
    step=0.5
)

min_reviews = st.sidebar.slider(
    "Minimum Review Count",
    min_value=int(dashboard_df["review_count"].min()),
    max_value=int(dashboard_df["review_count"].max()),
    value=int(dashboard_df["review_count"].min())
)

if "is_open" in dashboard_df.columns:
    open_status = st.sidebar.selectbox(
        "Restaurant Status",
        options=["All", "Open Only", "Closed / Inactive Only"]
    )
else:
    open_status = "All"

# Optional category filter
category_cols = [
    "is_fast_food",
    "is_breakfast_brunch",
    "is_coffee_tea",
    "is_bars",
    "is_pizza",
    "is_mexican",
    "is_chinese"
]

available_category_cols = [
    col for col in category_cols
    if col in dashboard_df.columns
]

category_display_map = {
    "is_fast_food": "Fast Food",
    "is_breakfast_brunch": "Breakfast / Brunch",
    "is_coffee_tea": "Coffee / Tea",
    "is_bars": "Bars",
    "is_pizza": "Pizza",
    "is_mexican": "Mexican",
    "is_chinese": "Chinese"
}

selected_categories = []

if available_category_cols:
    selected_categories = st.sidebar.multiselect(
        "Optional Category Filter",
        options=[category_display_map.get(col, col) for col in available_category_cols],
        default=[]
    )

# --------------------------------------------------
# Apply Filters
# --------------------------------------------------
filtered_df = dashboard_df[
    (dashboard_df["state"].isin(selected_states)) &
    (dashboard_df["dashboard_risk_level"].isin(selected_risk_levels)) &
    (dashboard_df["review_count"] >= min_reviews) &
    (dashboard_df["stars"] >= rating_range[0]) &
    (dashboard_df["stars"] <= rating_range[1])
].copy()

if "is_open" in filtered_df.columns:
    if open_status == "Open Only":
        filtered_df = filtered_df[filtered_df["is_open"] == 1]
    elif open_status == "Closed / Inactive Only":
        filtered_df = filtered_df[filtered_df["is_open"] == 0]

# Apply optional category filter
if selected_categories and available_category_cols:
    reverse_category_map = {
        display: col for col, display in category_display_map.items()
    }

    selected_category_cols = [
        reverse_category_map[cat]
        for cat in selected_categories
        if cat in reverse_category_map
    ]

    if selected_category_cols:
        category_mask = filtered_df[selected_category_cols].sum(axis=1) > 0
        filtered_df = filtered_df[category_mask].copy()

# --------------------------------------------------
# Empty Filter Safety
# --------------------------------------------------
if filtered_df.empty:
    st.warning("No records match the selected filters. Please adjust the sidebar filters.")
    st.stop()

# --------------------------------------------------
# KPI Cards
# --------------------------------------------------
st.markdown("## Executive Overview")

total_restaurants = len(filtered_df)
avg_rating = filtered_df["stars"].mean()
median_rating = filtered_df["stars"].median()
avg_reviews = filtered_df["review_count"].mean()

if "low_rating_flag" in filtered_df.columns:
    risk_rate = filtered_df["low_rating_flag"].mean() * 100
else:
    risk_rate = 0

if "opportunity_flag" in filtered_df.columns:
    opportunity_rate = filtered_df["opportunity_flag"].mean() * 100
else:
    opportunity_rate = 0

if "is_open" in filtered_df.columns:
    open_rate = filtered_df["is_open"].mean() * 100
else:
    open_rate = 0

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Restaurants", f"{total_restaurants:,.0f}")
col2.metric("Avg Rating", f"{avg_rating:.2f}")
col3.metric("Median Rating", f"{median_rating:.2f}")
col4.metric("Avg Reviews", f"{avg_reviews:,.0f}")
col5.metric("Risk Rate", f"{risk_rate:.1f}%")
col6.metric("Opportunity Rate", f"{opportunity_rate:.1f}%")

st.markdown(
    f"""
    **Executive Interpretation:**  
    The filtered dataset includes **{total_restaurants:,.0f} restaurants** with an average public rating of **{avg_rating:.2f}**.
    Based on the engineered low-rating risk flag, approximately **{risk_rate:.1f}%** of the selected restaurants show potential
    public performance risk. The opportunity rate is **{opportunity_rate:.1f}%**, representing restaurants with stronger rating
    and review signals.
    """
)

# --------------------------------------------------
# Risk Segmentation
# --------------------------------------------------
st.markdown("## Risk Segmentation")

left_col, right_col = st.columns(2)

with left_col:
    risk_counts = (
        filtered_df["dashboard_risk_level"]
        .value_counts()
        .reset_index()
    )
    risk_counts.columns = ["Risk Level", "Restaurant Count"]

    fig_risk = px.bar(
        risk_counts,
        x="Risk Level",
        y="Restaurant Count",
        title="Restaurant Count by Dashboard Risk Level"
    )

    st.plotly_chart(fig_risk, use_container_width=True)

with right_col:
    if "rating_group" in filtered_df.columns:
        rating_counts = (
            filtered_df["rating_group"]
            .value_counts()
            .reset_index()
        )
        rating_counts.columns = ["Rating Group", "Restaurant Count"]

        fig_rating = px.bar(
            rating_counts,
            x="Rating Group",
            y="Restaurant Count",
            title="Restaurant Count by Rating Group"
        )

        st.plotly_chart(fig_rating, use_container_width=True)
    else:
        fig_rating_hist = px.histogram(
            filtered_df,
            x="stars",
            nbins=10,
            title="Restaurant Rating Distribution"
        )
        st.plotly_chart(fig_rating_hist, use_container_width=True)

# --------------------------------------------------
# Rating and Review Volume Analysis
# --------------------------------------------------
st.markdown("## Rating and Review Volume Analysis")

scatter_hover_cols = [
    col for col in ["name", "city", "state", "stars", "review_count", "dashboard_risk_level"]
    if col in filtered_df.columns
]

fig_scatter = px.scatter(
    filtered_df,
    x="review_count",
    y="stars",
    color="dashboard_risk_level",
    hover_data=scatter_hover_cols,
    log_x=True,
    title="Restaurant Rating vs Review Volume"
)

fig_scatter.update_layout(
    xaxis_title="Review Count - Log Scale",
    yaxis_title="Star Rating"
)

st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown(
    """
    This chart helps separate restaurants with limited review history from restaurants with stronger public feedback volume.
    Lower-rated restaurants with higher review counts may represent more reliable risk signals because the rating is supported
    by more customer feedback.
    """
)

# --------------------------------------------------
# Market and Geography View
# --------------------------------------------------
st.markdown("## Market and Geography View")

state_summary = (
    filtered_df
    .groupby("state")
    .agg(
        restaurant_count=("business_id", "count") if "business_id" in filtered_df.columns else ("state", "count"),
        avg_rating=("stars", "mean"),
        avg_review_count=("review_count", "mean"),
        low_rating_rate=("low_rating_flag", "mean") if "low_rating_flag" in filtered_df.columns else ("stars", "mean")
    )
    .reset_index()
)

if "low_rating_flag" in filtered_df.columns:
    state_summary["low_rating_rate"] = state_summary["low_rating_rate"] * 100
else:
    state_summary["low_rating_rate"] = 0

left_col, right_col = st.columns(2)

with left_col:
    fig_state = px.bar(
        state_summary.sort_values("restaurant_count", ascending=False),
        x="state",
        y="restaurant_count",
        title="Restaurant Count by State"
    )
    st.plotly_chart(fig_state, use_container_width=True)

with right_col:
    fig_state_risk = px.bar(
        state_summary.sort_values("low_rating_rate", ascending=False),
        x="state",
        y="low_rating_rate",
        title="Low Rating Risk Rate by State"
    )
    fig_state_risk.update_layout(
        yaxis_title="Low Rating Risk Rate (%)",
        xaxis_title="State"
    )
    st.plotly_chart(fig_state_risk, use_container_width=True)

st.markdown("### State Market Summary")

state_display = state_summary.sort_values(
    by="low_rating_rate",
    ascending=False
).copy()

state_display["avg_rating"] = state_display["avg_rating"].round(2)
state_display["avg_review_count"] = state_display["avg_review_count"].round(0)
state_display["low_rating_rate"] = state_display["low_rating_rate"].round(1)

st.dataframe(
    state_display,
    use_container_width=True
)

# --------------------------------------------------
# Restaurant Map
# --------------------------------------------------
st.markdown("## Restaurant Map")

map_df = filtered_df.dropna(subset=["latitude", "longitude"]).copy() if {"latitude", "longitude"}.issubset(filtered_df.columns) else pd.DataFrame()

if len(map_df) > 0:
    map_hover_cols = [
        col for col in ["city", "state", "stars", "review_count", "dashboard_risk_level"]
        if col in map_df.columns
    ]

    fig_map = px.scatter_mapbox(
        map_df,
        lat="latitude",
        lon="longitude",
        hover_name="name" if "name" in map_df.columns else None,
        hover_data=map_hover_cols,
        color="dashboard_risk_level",
        zoom=3,
        height=600,
        title="Restaurant Locations by Risk Level"
    )

    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("No latitude and longitude data available for the selected filters.")

# --------------------------------------------------
# Category Risk View
# --------------------------------------------------
st.markdown("## Category Risk View")

category_summary = []

for col in available_category_cols:
    category_df = filtered_df[filtered_df[col] == 1]

    if len(category_df) > 0:
        category_summary.append({
            "category": category_display_map.get(col, col.replace("is_", "").replace("_", " ").title()),
            "restaurant_count": len(category_df),
            "avg_rating": category_df["stars"].mean(),
            "avg_review_count": category_df["review_count"].mean(),
            "low_rating_rate": category_df["low_rating_flag"].mean() * 100
                if "low_rating_flag" in category_df.columns else 0
        })

category_summary_df = pd.DataFrame(category_summary)

if not category_summary_df.empty:
    category_summary_df["avg_rating"] = category_summary_df["avg_rating"].round(2)
    category_summary_df["avg_review_count"] = category_summary_df["avg_review_count"].round(0)
    category_summary_df["low_rating_rate"] = category_summary_df["low_rating_rate"].round(1)

    fig_category = px.bar(
        category_summary_df.sort_values("low_rating_rate", ascending=False),
        x="category",
        y="low_rating_rate",
        title="Low Rating Risk Rate by Restaurant Category"
    )

    fig_category.update_layout(
        xaxis_title="Category",
        yaxis_title="Low Rating Risk Rate (%)"
    )

    st.plotly_chart(fig_category, use_container_width=True)

    st.dataframe(category_summary_df, use_container_width=True)

    st.markdown(
        """
        This section compares risk patterns across major restaurant categories.
        It helps identify whether certain restaurant segments show higher public-rating risk than others.
        """
    )
else:
    st.info("No category indicator columns are available for the selected data.")

# --------------------------------------------------
# Priority Restaurant Lists
# --------------------------------------------------
st.markdown("## Priority Restaurant Lists")

risk_table_cols = [
    "name",
    "city",
    "state",
    "stars",
    "review_count",
    "dashboard_risk_level",
    "basic_risk_score",
    "rating_vs_state_avg",
    "rating_vs_city_avg",
    "review_count_vs_state_avg",
    "review_count_vs_city_avg"
]

available_risk_cols = [
    col for col in risk_table_cols
    if col in filtered_df.columns
]

left_col, right_col = st.columns(2)

with left_col:
    st.markdown("### Highest Risk Restaurants")

    if "basic_risk_score" in filtered_df.columns:
        top_risk = filtered_df[available_risk_cols].sort_values(
            by=["basic_risk_score", "review_count"],
            ascending=[False, False]
        ).head(25)
    else:
        top_risk = filtered_df[available_risk_cols].sort_values(
            by=["stars", "review_count"],
            ascending=[True, False]
        ).head(25)

    st.dataframe(top_risk, use_container_width=True)

with right_col:
    st.markdown("### Strongest Opportunity Restaurants")

    if "opportunity_flag" in filtered_df.columns:
        opportunity_df = filtered_df[filtered_df["opportunity_flag"] == 1].copy()

        if opportunity_df.empty:
            opportunity_df = filtered_df.copy()

        top_opportunity = opportunity_df[available_risk_cols].sort_values(
            by=["stars", "review_count"],
            ascending=[False, False]
        ).head(25)
    else:
        top_opportunity = filtered_df[available_risk_cols].sort_values(
            by=["stars", "review_count"],
            ascending=[False, False]
        ).head(25)

    st.dataframe(top_opportunity, use_container_width=True)

# --------------------------------------------------
# Full Restaurant Risk Detail
# --------------------------------------------------
st.markdown("## Restaurant Risk Detail")

sort_options = [
    col for col in [
        "basic_risk_score",
        "stars",
        "review_count",
        "rating_vs_state_avg",
        "rating_vs_city_avg"
    ]
    if col in filtered_df.columns
]

if sort_options:
    sort_col = st.selectbox(
        "Sort restaurant table by",
        options=sort_options,
        index=0
    )
else:
    sort_col = "stars"

ascending_default = False if sort_col in ["basic_risk_score", "review_count"] else True

risk_table = filtered_df[available_risk_cols].sort_values(
    by=sort_col,
    ascending=ascending_default
)

st.dataframe(risk_table.head(250), use_container_width=True)

# --------------------------------------------------
# Denny's Validation Section
# --------------------------------------------------
st.markdown("## Denny's Validation View")

if not dennys_df.empty:
    st.markdown(
        """
        The Denny's validation file is used as a separate enterprise benchmark.
        It is not directly merged into the public restaurant universe because it represents internal restaurant performance data.
        The purpose is to compare whether the public risk framework is directionally useful when reviewed against enterprise
        restaurant performance signals.
        """
    )

    col_a, col_b, col_c = st.columns(3)

    col_a.metric("Denny's Records", f"{len(dennys_df):,.0f}")

    dennys_numeric_cols = dennys_df.select_dtypes(include="number").columns.tolist()

    if len(dennys_numeric_cols) > 0:
        selected_metric = st.selectbox(
            "Select Denny's validation metric",
            dennys_numeric_cols
        )

        col_b.metric(
            f"Avg {selected_metric}",
            f"{dennys_df[selected_metric].mean():.2f}"
        )

        col_c.metric(
            f"Median {selected_metric}",
            f"{dennys_df[selected_metric].median():.2f}"
        )

        fig_dennys = px.histogram(
            dennys_df,
            x=selected_metric,
            nbins=30,
            title=f"Denny's Validation Metric Distribution: {selected_metric}"
        )

        st.plotly_chart(fig_dennys, use_container_width=True)

    st.markdown("### Denny's Validation Data Preview")
    st.dataframe(dennys_df.head(100), use_container_width=True)

else:
    st.info("Denny's validation file was not found or is empty.")

# --------------------------------------------------
# Methodology
# --------------------------------------------------
st.markdown("## Methodology Summary")

with st.expander("View Dashboard Methodology"):
    st.markdown(
        """
        **Data Source:**  
        The main dashboard uses a cleaned public restaurant dataset prepared from Yelp-style restaurant business data.

        **Feature Engineering:**  
        The dashboard includes engineered fields such as rating group, review volume group, low-rating flag, closed flag,
        basic risk score, opportunity flag, state and city market averages, and category indicators.

        **Risk Logic:**  
        Restaurants are segmented into dashboard risk levels using rating-based risk flags, open/closed status,
        and the engineered basic risk score.

        **Validation Approach:**  
        Public health inspection data was explored as a possible validation source. However, due to geographic and matching
        limitations, it was not used as the primary validation framework. A separate Denny's validation dataset was prepared
        to support directional comparison against enterprise restaurant performance data.

        **Business Use:**  
        This dashboard is designed as a decision-support tool for identifying restaurants that may require additional
        operational review, market-level monitoring, or deeper customer feedback analysis.
        """
    )

# --------------------------------------------------
# Download
# --------------------------------------------------
st.markdown("## Download Dashboard Data")

st.download_button(
    label="Download Filtered Dashboard Data",
    data=filtered_df.to_csv(index=False),
    file_name="filtered_capstone_dashboard_data.csv",
    mime="text/csv"
)