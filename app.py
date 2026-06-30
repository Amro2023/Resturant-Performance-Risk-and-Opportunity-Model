import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# ------------------------------------------------------------
# Page setup
# ------------------------------------------------------------
st.set_page_config(
    page_title="Restaurant Performance Risk & Opportunity Dashboard",
    page_icon="🍽️",
    layout="wide"
)


# ------------------------------------------------------------
# Data paths
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

MAIN_DATA_PATH = DATA_DIR / "capstone_dashboard_dataset.csv"
VALIDATION_DATA_PATH = DATA_DIR / "anonymous_brand_restaurant_validation.csv"


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def clean_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def pct(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:.1%}"


def num(value: float, decimals: int = 1) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}"


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()

    with st.sidebar:
        st.header("Dashboard Filters")

        if "state" in filtered.columns:
            states = sorted(filtered["state"].dropna().astype(str).unique().tolist())
            selected_states = st.multiselect("State", states, default=[])
            if selected_states:
                filtered = filtered[filtered["state"].astype(str).isin(selected_states)]

        if "dashboard_risk_level" in filtered.columns:
            risk_levels = sorted(filtered["dashboard_risk_level"].dropna().astype(str).unique().tolist())
            selected_risk = st.multiselect("Risk Level", risk_levels, default=[])
            if selected_risk:
                filtered = filtered[filtered["dashboard_risk_level"].astype(str).isin(selected_risk)]

        if "stars" in filtered.columns:
            min_rating = float(np.nanmin(filtered["stars"])) if filtered["stars"].notna().any() else 0.0
            max_rating = float(np.nanmax(filtered["stars"])) if filtered["stars"].notna().any() else 5.0
            rating_range = st.slider(
                "Rating Range",
                min_value=0.0,
                max_value=5.0,
                value=(max(0.0, min_rating), min(5.0, max_rating)),
                step=0.1
            )
            filtered = filtered[(filtered["stars"] >= rating_range[0]) & (filtered["stars"] <= rating_range[1])]

        if "review_count" in filtered.columns:
            max_reviews = int(filtered["review_count"].max()) if filtered["review_count"].notna().any() else 0
            min_reviews_selected = st.number_input(
                "Minimum Review Count",
                min_value=0,
                max_value=max_reviews if max_reviews > 0 else 1,
                value=0,
                step=10
            )
            filtered = filtered[filtered["review_count"] >= min_reviews_selected]

        category_options = {
            "Fast Food": "is_fast_food",
            "Breakfast / Brunch": "is_breakfast_brunch",
            "Coffee / Tea": "is_coffee_tea",
            "Bars": "is_bars",
            "Pizza": "is_pizza",
            "Mexican": "is_mexican",
            "Chinese": "is_chinese",
        }

        available_categories = {
            label: col for label, col in category_options.items()
            if col in filtered.columns
        }

        selected_categories = st.multiselect("Category", list(available_categories.keys()), default=[])

        if selected_categories:
            category_cols = [available_categories[label] for label in selected_categories]
            filtered = filtered[filtered[category_cols].fillna(0).sum(axis=1) > 0]

        if "is_open" in filtered.columns:
            open_filter = st.selectbox("Open Status", ["All", "Open Only", "Closed / Inactive Only"])
            if open_filter == "Open Only":
                filtered = filtered[filtered["is_open"] == 1]
            elif open_filter == "Closed / Inactive Only":
                filtered = filtered[filtered["is_open"] == 0]

    return filtered


# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------
dashboard_df = load_csv(MAIN_DATA_PATH)
validation_df = load_csv(VALIDATION_DATA_PATH)

required_numeric_cols = [
    "stars",
    "review_count",
    "log_review_count",
    "latitude",
    "longitude",
    "low_rating_flag",
    "low_review_count_flag",
    "closed_flag",
    "basic_risk_score",
    "high_rating_flag",
    "high_review_count_flag",
    "opportunity_flag",
    "state_restaurant_count",
    "city_restaurant_count",
    "state_avg_rating",
    "city_avg_rating",
    "rating_vs_state_avg",
    "rating_vs_city_avg",
    "state_avg_review_count",
    "city_avg_review_count",
    "review_count_vs_state_avg",
    "review_count_vs_city_avg",
    "is_fast_food",
    "is_breakfast_brunch",
    "is_coffee_tea",
    "is_bars",
    "is_pizza",
    "is_mexican",
    "is_chinese"
]

dashboard_df = clean_numeric(dashboard_df, required_numeric_cols)

if not validation_df.empty:
    validation_numeric_cols = validation_df.columns.tolist()
    validation_df = clean_numeric(validation_df, validation_numeric_cols)


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
st.title("Restaurant Performance Risk & Opportunity Dashboard")
st.caption("A public-data risk screening tool with anonymous brand restaurant validation support.")

if dashboard_df.empty:
    st.error(
        "Main dashboard dataset was not found. Place capstone_dashboard_dataset.csv inside data/processed/."
    )
    st.stop()

filtered_df = apply_filters(dashboard_df)


# ------------------------------------------------------------
# Executive overview
# ------------------------------------------------------------
st.subheader("1. Executive Overview")

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

total_restaurants = len(filtered_df)
avg_rating = filtered_df["stars"].mean() if "stars" in filtered_df.columns else np.nan
median_rating = filtered_df["stars"].median() if "stars" in filtered_df.columns else np.nan
avg_reviews = filtered_df["review_count"].mean() if "review_count" in filtered_df.columns else np.nan
risk_rate = filtered_df["low_rating_flag"].mean() if "low_rating_flag" in filtered_df.columns else np.nan
opportunity_rate = filtered_df["opportunity_flag"].mean() if "opportunity_flag" in filtered_df.columns else np.nan

kpi1.metric("Restaurants", f"{total_restaurants:,.0f}")
kpi2.metric("Avg Rating", num(avg_rating, 2))
kpi3.metric("Median Rating", num(median_rating, 2))
kpi4.metric("Avg Review Count", num(avg_reviews, 0))
kpi5.metric("Low-Rating Risk Rate", pct(risk_rate))
kpi6.metric("Opportunity Rate", pct(opportunity_rate))

st.info(
    "Use the filters on the left to review restaurant performance signals by market, risk level, rating range, review volume, and category."
)


# ------------------------------------------------------------
# Statistical findings summary
# ------------------------------------------------------------
st.subheader("2. Statistical Validation Summary")

stat_col1, stat_col2, stat_col3 = st.columns(3)

stat_col1.metric(
    "Negative Review % Test",
    "p < 0.001",
    "High-risk restaurants showed higher negative review share"
)

stat_col2.metric(
    "Anonymous Brand Rating Test",
    "p < 0.001",
    "Higher internal-risk locations had lower public rating"
)

stat_col3.metric(
    "Model ROC AUC",
    "0.994",
    "Random Forest model performance"
)

with st.expander("View statistical interpretation"):
    st.markdown(
        """
        - The public-data hypothesis test compared negative review percentage between low-rating-risk and non-low-rating-risk restaurants.
        - The anonymous brand restaurant validation test compared guest-facing rating indicators between higher internal-risk and lower internal-risk groups.
        - The ROC AUC result shows that the trained model had strong separation between lower-risk and higher-risk restaurant classes.
        - These tests support the dashboard as a screening and prioritization tool, not as a standalone operational diagnosis.
        """
    )


# ------------------------------------------------------------
# Risk segmentation
# ------------------------------------------------------------
st.subheader("3. Risk Segmentation")

chart_col1, chart_col2 = st.columns(2)

if "dashboard_risk_level" in filtered_df.columns:
    risk_counts = (
        filtered_df["dashboard_risk_level"]
        .value_counts(dropna=False)
        .rename_axis("Risk Level")
        .reset_index(name="Restaurant Count")
    )

    fig_risk = px.bar(
        risk_counts,
        x="Risk Level",
        y="Restaurant Count",
        title="Restaurants by Dashboard Risk Level",
        text="Restaurant Count"
    )

    chart_col1.plotly_chart(fig_risk, use_container_width=True)

if "rating_group" in filtered_df.columns:
    rating_counts = (
        filtered_df["rating_group"]
        .value_counts(dropna=False)
        .rename_axis("Rating Group")
        .reset_index(name="Restaurant Count")
    )

    fig_rating_group = px.bar(
        rating_counts,
        x="Rating Group",
        y="Restaurant Count",
        title="Restaurants by Rating Group",
        text="Restaurant Count"
    )

    chart_col2.plotly_chart(fig_rating_group, use_container_width=True)


# ------------------------------------------------------------
# Rating and review volume analysis
# ------------------------------------------------------------
st.subheader("4. Rating and Review Volume Analysis")

scatter_cols = [
    col for col in ["name", "city", "state", "stars", "review_count", "dashboard_risk_level"]
    if col in filtered_df.columns
]

if {"stars", "review_count"}.issubset(filtered_df.columns):
    fig_scatter = px.scatter(
        filtered_df,
        x="review_count",
        y="stars",
        color="dashboard_risk_level" if "dashboard_risk_level" in filtered_df.columns else None,
        hover_data=scatter_cols,
        log_x=True,
        title="Rating vs. Review Count"
    )

    fig_scatter.update_layout(
        xaxis_title="Review Count - Log Scale",
        yaxis_title="Star Rating"
    )

    st.plotly_chart(fig_scatter, use_container_width=True)

hist_col1, hist_col2 = st.columns(2)

if "stars" in filtered_df.columns:
    fig_hist_rating = px.histogram(
        filtered_df,
        x="stars",
        nbins=20,
        title="Rating Distribution"
    )

    hist_col1.plotly_chart(fig_hist_rating, use_container_width=True)

if "review_count" in filtered_df.columns:
    fig_hist_reviews = px.histogram(
        filtered_df[filtered_df["review_count"].notna()],
        x="review_count",
        nbins=50,
        title="Review Count Distribution"
    )

    fig_hist_reviews.update_layout(xaxis_title="Review Count")

    hist_col2.plotly_chart(fig_hist_reviews, use_container_width=True)


# ------------------------------------------------------------
# Market and geography view
# ------------------------------------------------------------
st.subheader("5. Market and Geography View")

if "state" in filtered_df.columns and "low_rating_flag" in filtered_df.columns:
    state_summary = (
        filtered_df.groupby("state", dropna=False)
        .agg(
            restaurant_count=("business_id", "count") if "business_id" in filtered_df.columns else ("state", "size"),
            avg_rating=("stars", "mean") if "stars" in filtered_df.columns else ("low_rating_flag", "mean"),
            low_rating_risk_rate=("low_rating_flag", "mean"),
            avg_review_count=("review_count", "mean") if "review_count" in filtered_df.columns else ("low_rating_flag", "mean")
        )
        .reset_index()
        .sort_values("restaurant_count", ascending=False)
    )

    market_col1, market_col2 = st.columns(2)

    top_states = state_summary.head(20)

    fig_state_count = px.bar(
        top_states,
        x="state",
        y="restaurant_count",
        title="Top States by Restaurant Count",
        text="restaurant_count"
    )

    market_col1.plotly_chart(fig_state_count, use_container_width=True)

    min_count = st.slider(
        "Minimum state restaurant count for risk-rate chart",
        10,
        1000,
        100,
        step=10
    )

    risk_states = (
        state_summary[state_summary["restaurant_count"] >= min_count]
        .sort_values("low_rating_risk_rate", ascending=False)
        .head(20)
    )

    fig_state_risk = px.bar(
        risk_states,
        x="state",
        y="low_rating_risk_rate",
        title="Highest Low-Rating Risk Rate by State",
        text="low_rating_risk_rate"
    )

    fig_state_risk.update_traces(texttemplate="%{text:.1%}")
    fig_state_risk.update_layout(yaxis_tickformat=".0%")

    market_col2.plotly_chart(fig_state_risk, use_container_width=True)

    st.dataframe(
        state_summary.style.format(
            {
                "avg_rating": "{:.2f}",
                "low_rating_risk_rate": "{:.1%}",
                "avg_review_count": "{:.0f}"
            }
        ),
        use_container_width=True
    )


# ------------------------------------------------------------
# Restaurant map
# ------------------------------------------------------------
st.subheader("6. Restaurant Map")

map_required = {"latitude", "longitude"}

if map_required.issubset(filtered_df.columns):
    map_df = filtered_df.dropna(subset=["latitude", "longitude"]).copy()

    if not map_df.empty:
        map_hover = [
            col for col in ["name", "city", "state", "stars", "review_count", "dashboard_risk_level"]
            if col in map_df.columns
        ]

        fig_map = px.scatter_mapbox(
            map_df,
            lat="latitude",
            lon="longitude",
            color="dashboard_risk_level" if "dashboard_risk_level" in map_df.columns else None,
            hover_data=map_hover,
            zoom=3,
            height=550,
            title="Restaurant Locations by Risk Level"
        )

        fig_map.update_layout(mapbox_style="open-street-map")
        fig_map.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})

        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No valid latitude and longitude records available for the current filter selection.")


# ------------------------------------------------------------
# Category risk view
# ------------------------------------------------------------
st.subheader("7. Category Risk View")

category_map = {
    "Fast Food": "is_fast_food",
    "Breakfast / Brunch": "is_breakfast_brunch",
    "Coffee / Tea": "is_coffee_tea",
    "Bars": "is_bars",
    "Pizza": "is_pizza",
    "Mexican": "is_mexican",
    "Chinese": "is_chinese",
}

category_rows = []

for label, col in category_map.items():
    if col in filtered_df.columns and "low_rating_flag" in filtered_df.columns:
        temp = filtered_df[filtered_df[col].fillna(0) == 1]

        if len(temp) > 0:
            category_rows.append(
                {
                    "Category": label,
                    "Restaurant Count": len(temp),
                    "Low-Rating Risk Rate": temp["low_rating_flag"].mean(),
                    "Average Rating": temp["stars"].mean() if "stars" in temp.columns else np.nan,
                    "Average Review Count": temp["review_count"].mean() if "review_count" in temp.columns else np.nan,
                }
            )

category_summary = pd.DataFrame(category_rows)

if not category_summary.empty:
    category_summary = category_summary.sort_values("Low-Rating Risk Rate", ascending=False)

    fig_category = px.bar(
        category_summary,
        x="Category",
        y="Low-Rating Risk Rate",
        text="Low-Rating Risk Rate",
        title="Low-Rating Risk Rate by Restaurant Category"
    )

    fig_category.update_traces(texttemplate="%{text:.1%}")
    fig_category.update_layout(yaxis_tickformat=".0%")

    st.plotly_chart(fig_category, use_container_width=True)

    st.dataframe(
        category_summary.style.format(
            {
                "Low-Rating Risk Rate": "{:.1%}",
                "Average Rating": "{:.2f}",
                "Average Review Count": "{:.0f}"
            }
        ),
        use_container_width=True
    )
else:
    st.warning("No category indicator fields are available for the current filter selection.")


# ------------------------------------------------------------
# Priority restaurant lists
# ------------------------------------------------------------
st.subheader("8. Priority Restaurant Lists")

priority_col1, priority_col2 = st.columns(2)

priority_cols = [
    col for col in [
        "name",
        "city",
        "state",
        "stars",
        "review_count",
        "dashboard_risk_level",
        "basic_risk_score",
        "rating_vs_city_avg",
        "review_count_vs_city_avg"
    ]
    if col in filtered_df.columns
]

if priority_cols:
    risk_sort_cols = [
        col for col in ["basic_risk_score", "review_count"]
        if col in filtered_df.columns
    ]

    if risk_sort_cols:
        high_risk_table = filtered_df.sort_values(
            risk_sort_cols,
            ascending=[False] * len(risk_sort_cols)
        ).head(25)
    else:
        high_risk_table = filtered_df.head(25)

    priority_col1.markdown("**Highest Priority Risk Review**")
    priority_col1.dataframe(high_risk_table[priority_cols], use_container_width=True)

    if "opportunity_flag" in filtered_df.columns:
        opportunity_df = filtered_df[filtered_df["opportunity_flag"] == 1].copy()
    else:
        opportunity_df = filtered_df.copy()

    opportunity_sort_cols = [
        col for col in ["stars", "review_count"]
        if col in opportunity_df.columns
    ]

    if opportunity_sort_cols:
        opportunity_table = opportunity_df.sort_values(
            opportunity_sort_cols,
            ascending=[False] * len(opportunity_sort_cols)
        ).head(25)
    else:
        opportunity_table = opportunity_df.head(25)

    priority_col2.markdown("**Strongest Opportunity Restaurants**")
    priority_col2.dataframe(opportunity_table[priority_cols], use_container_width=True)


# ------------------------------------------------------------
# Anonymous brand restaurant validation view
# ------------------------------------------------------------
st.subheader("9. Anonymous Brand Restaurant Validation View")

if validation_df.empty:
    st.warning(
        "Anonymous brand restaurant validation file was not found. Place anonymous_brand_restaurant_validation.csv inside data/processed/."
    )
else:
    st.markdown(
        "This section uses a separate anonymized brand restaurant dataset for directional validation. The file is not blended into the public restaurant universe."
    )

    numeric_validation_cols = validation_df.select_dtypes(include=[np.number]).columns.tolist()

    val_kpi1, val_kpi2, val_kpi3, val_kpi4 = st.columns(4)

    val_kpi1.metric("Validation Records", f"{len(validation_df):,.0f}")

    if "internal_high_risk_flag" in validation_df.columns:
        val_kpi2.metric("Internal High-Risk Rate", pct(validation_df["internal_high_risk_flag"].mean()))
    else:
        val_kpi2.metric("Internal High-Risk Rate", "N/A")

    if "Overall Quintile" in validation_df.columns:
        val_kpi3.metric("Avg Overall Quintile", num(validation_df["Overall Quintile"].mean(), 2))
    else:
        val_kpi3.metric("Avg Overall Quintile", "N/A")

    if "Google Rating L90D" in validation_df.columns:
        val_kpi4.metric("Avg Public Rating", num(validation_df["Google Rating L90D"].mean(), 2))
    else:
        val_kpi4.metric("Avg Public Rating", "N/A")

    if numeric_validation_cols:
        selected_metric = st.selectbox("Select validation metric", numeric_validation_cols)

        fig_val_hist = px.histogram(
            validation_df,
            x=selected_metric,
            title=f"Distribution of {selected_metric}"
        )

        st.plotly_chart(fig_val_hist, use_container_width=True)

        if "Overall Quintile" in validation_df.columns and selected_metric != "Overall Quintile":
            fig_val_box = px.box(
                validation_df,
                x="Overall Quintile",
                y=selected_metric,
                title=f"{selected_metric} by Overall Quintile"
            )

            st.plotly_chart(fig_val_box, use_container_width=True)

    st.dataframe(validation_df.head(100), use_container_width=True)


# ------------------------------------------------------------
# Methodology summary
# ------------------------------------------------------------
st.subheader("10. Methodology Summary")

with st.expander("Open methodology notes"):
    st.markdown(
        """
        **Purpose:** Build a restaurant performance risk and opportunity dashboard using public restaurant data and an anonymized validation layer.

        **Public-data framework:** The dashboard uses restaurant rating, review count, open status, geography, category indicators, and market comparison fields.

        **Risk logic:** Restaurants are grouped into dashboard risk levels using low-rating flags, open status, and engineered risk scoring.

        **Validation approach:** Public health inspection data was explored, but data completeness and matching limitations reduced its usefulness for broad validation. A separate anonymous brand restaurant dataset is used as directional validation to compare public-facing signals against internal performance indicators.

        **Business use:** This dashboard should be used as a first-level screening tool. Restaurants flagged as high risk should be reviewed further with internal operating metrics, customer comments, field observations, and brand standards data.
        """
    )

st.caption("Prepared for DATA 6999 Capstone Project | Restaurant Performance Risk and Opportunity Model")