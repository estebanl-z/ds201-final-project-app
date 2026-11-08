from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="US Airfare & Passenger Demand", layout="wide")

# Finds the data file no matter which folder you run the app from
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "merged_fare_passengers.csv"

# Colors and labels used across all charts
FARE_COLOR = "#E76F51"   # orange-red
PAX_COLOR = "#457B9D"    # steel blue
COVID_START, COVID_END = pd.Timestamp("2020-01-01"), pd.Timestamp("2021-07-01")

METRICS = {
    "Average fare ($)": ("national_avg_fare", FARE_COLOR, "Average Airfare (USD)"),
    "Passengers (millions)": ("passengers_millions", PAX_COLOR, "Quarterly Passenger Enplanements (Millions)"),
}


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    # one date per quarter, so the x-axis can show years
    df["date"] = pd.to_datetime(dict(year=df["year"], month=3 * (df["quarter"] - 1) + 1, day=1))
    return df


def style_axes(ax, title=None):
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, fontsize=14, fontweight="bold", pad=12)


def year_axis(ax):
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlabel("Year", fontsize=11)


def shade_covid(ax):
    ax.axvspan(COVID_START, COVID_END, color="gray", alpha=0.15, zorder=0)


def trend_chart(d, metric, show_covid):
    fig, ax = plt.subplots(figsize=(12, 5))
    if metric == "Both (dual axis)":
        ax.plot(d["date"], d["national_avg_fare"], color=FARE_COLOR, marker="o",
                linewidth=2.2, label="Average Airfare")
        ax.set_ylabel("Average Airfare (USD)", color=FARE_COLOR, fontsize=11)
        ax.tick_params(axis="y", labelcolor=FARE_COLOR)
        ax2 = ax.twinx()
        ax2.plot(d["date"], d["passengers_millions"], color=PAX_COLOR, marker="s",
                 linewidth=2.2, label="Passenger Demand")
        ax2.set_ylabel("Quarterly Passenger Enplanements (Millions)", color=PAX_COLOR, fontsize=11)
        ax2.tick_params(axis="y", labelcolor=PAX_COLOR)
        lines = ax.get_lines() + ax2.get_lines()
        ax.legend(lines, [l.get_label() for l in lines], loc="upper left")
        title = "U.S. Domestic Airfare and Passenger Demand Trends"
    else:
        col, color, label = METRICS[metric]
        ax.plot(d["date"], d[col], color=color, marker="o", linewidth=2.2)
        ax.set_ylabel(label, color=color, fontsize=11)
        ax.tick_params(axis="y", labelcolor=color)
        title = f"U.S. Domestic {metric.split(' (')[0].title()} by Quarter"
    if show_covid:
        shade_covid(ax)
    style_axes(ax, title)
    year_axis(ax)
    fig.tight_layout()
    return fig


def seasonal_chart(d, metric, exclude_covid):
    """Heatmap: each quarter's % deviation from its own year's average."""
    col, _, _ = METRICS[metric]
    s = d.copy()
    if exclude_covid:
        s = s[~s["year"].isin([2020, 2021])]
    s = s.dropna(subset=[col])
    s = s[s.groupby("year")[col].transform("count") == 4]   # complete years only
    if s.empty:
        return None
    s["dev"] = (s[col] / s.groupby("year")[col].transform("mean") - 1) * 100
    pivot = s.pivot(index="year", columns="quarter", values="dev")
    pivot.columns = [f"Q{q}" for q in pivot.columns]
    lim = max(5, float(pivot.abs().max().max()))
    fig, ax = plt.subplots(figsize=(8, max(3, 0.5 * len(pivot) + 1.5)))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="RdBu_r", center=0, vmin=-lim, vmax=lim,
                linewidths=0.5, linecolor="white", ax=ax,
                cbar_kws={"label": "Deviation from Yearly Quarterly Average (%)"})
    suffix = " (Excluding 2020-2021)" if exclude_covid else ""
    ax.set_title(f"Seasonal {metric.split(' (')[0].title()} Pattern{suffix}", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Quarter")
    ax.set_ylabel("Year")
    ax.tick_params(axis="y", rotation=0)
    fig.tight_layout()
    return fig


def main():
    df = load_data()

    st.title("US Airfare and Passenger Demand")
    st.write("How have airline ticket prices changed, and how are they related to passenger demand?")

    # --- Sidebar controls ---
    st.sidebar.header("Controls")
    years = st.sidebar.slider("Year range", int(df["year"].min()), int(df["year"].max()), (2015, 2025))
    metric = st.sidebar.selectbox("Metric", ["Both (dual axis)"] + list(METRICS))
    show_covid = st.sidebar.checkbox("Highlight COVID-19 period", value=True)
    exclude_covid = st.sidebar.checkbox("Exclude 2020-2021 from seasonal chart", value=True)

    d = df[(df["year"] >= years[0]) & (df["year"] <= years[1])].reset_index(drop=True)

    # --- Chart 1: trend over time ---
    st.subheader("Trends over time")
    st.pyplot(trend_chart(d, metric, show_covid))

    # --- Chart 2: seasonal pattern ---
    st.subheader("Seasonal pattern")
    seasonal_metric = "Average fare ($)" if metric == "Both (dual axis)" else metric
    st.caption("Each cell shows how far a quarter is from its own year's average, "
               "which removes the long-term trend and leaves the seasonal pattern.")
    fig2 = seasonal_chart(d, seasonal_metric, exclude_covid)
    if fig2 is None:
        st.info("No complete years in the selected range. Widen the year range.")
    else:
        st.pyplot(fig2)
        if metric == "Both (dual axis)":
            st.caption("Showing fares. Pick Passengers in the Metric menu to see passenger demand.")


main()