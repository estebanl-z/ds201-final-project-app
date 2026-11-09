"""Streamlit dashboard: US domestic airfare and passenger demand."""
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="US Airfare & Passenger Demand", layout="wide")

DATA_PATH = (Path(__file__).resolve().parent.parent / "data"
             / "merged_fare_passengers.csv")
REPO_URL = "https://github.com/estebanl-z/ds201-final-project-appgit remote set-url origin https://github.com/estebanl-z/ds201-final-project-app.git
git remote -v"
TEAM = "Luke and Angelina"  # replace with full names if required

FARE_COLOR = "#E76F51"  # orange-red, used for fares
PAX_COLOR = "#457B9D"   # steel blue, used for passengers
COVID_YEARS = [2020, 2021]
COVID_START = pd.Timestamp("2020-01-01")
COVID_END = pd.Timestamp("2021-07-01")

# metric name -> (column, color, axis label)
METRICS = {
    "Average fare ($)": ("national_avg_fare", FARE_COLOR,
                         "Average Airfare (USD)"),
    "Passengers (millions)": ("passengers_millions", PAX_COLOR,
                              "Quarterly Passenger Enplanements (Millions)"),
}


@st.cache_data
def load_data():
    """Read the merged quarterly file and add one date per quarter."""
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(
        dict(year=df["year"], month=3 * (df["quarter"] - 1) + 1, day=1))
    return df


# ---------- chart helpers ----------
def style_axes(ax, title):
    """Light grid and bold title shared by all charts."""
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)


def year_axis(ax):
    """Label the x-axis with one tick per year."""
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlabel("Year", fontsize=11)


def shade_covid(ax):
    """Gray band with a text label over the COVID-19 period."""
    ax.axvspan(COVID_START, COVID_END, color="gray", alpha=0.15, zorder=0)
    middle = COVID_START + (COVID_END - COVID_START) / 2
    ax.text(middle, 0.97, "COVID-19", transform=ax.get_xaxis_transform(),
            ha="center", va="top", fontsize=10, fontweight="bold",
            color="dimgray", zorder=5)


def trend_chart(d, metric, show_covid):
    """Line chart of one metric, or both on a dual axis."""
    fig, ax = plt.subplots(figsize=(12, 5))
    if metric == "Both (dual axis)":
        ax.plot(d["date"], d["national_avg_fare"], color=FARE_COLOR,
                marker="o", linewidth=2.2, label="Average Airfare")
        ax.set_ylabel("Average Airfare (USD)", color=FARE_COLOR)
        ax.tick_params(axis="y", labelcolor=FARE_COLOR)
        ax2 = ax.twinx()
        ax2.plot(d["date"], d["passengers_millions"], color=PAX_COLOR,
                 marker="s", linewidth=2.2, label="Passenger Demand")
        ax2.set_ylabel("Quarterly Passenger Enplanements (Millions)",
                       color=PAX_COLOR)
        ax2.tick_params(axis="y", labelcolor=PAX_COLOR)
        lines = ax.get_lines() + ax2.get_lines()
        ax.legend(lines, [line.get_label() for line in lines],
                  loc="upper left")
        title = "U.S. Domestic Airfare and Passenger Demand Trends"
    else:
        col, color, label = METRICS[metric]
        ax.plot(d["date"], d[col], color=color, marker="o", linewidth=2.2)
        ax.set_ylabel(label, color=color)
        ax.tick_params(axis="y", labelcolor=color)
        title = f"U.S. Domestic {metric.split(' (')[0].title()} by Quarter"
    if show_covid:
        shade_covid(ax)
    style_axes(ax, title)
    year_axis(ax)
    fig.tight_layout()
    return fig


def deviation_table(d, col, exclude_covid):
    """Each quarter's % deviation from its own year's average."""
    s = d.copy()
    if exclude_covid:
        s = s[~s["year"].isin(COVID_YEARS)]
    s = s.dropna(subset=[col])
    s = s[s.groupby("year")[col].transform("count") == 4]  # full years only
    if s.empty:
        return None
    s["dev"] = (s[col] / s.groupby("year")[col].transform("mean") - 1) * 100
    pivot = s.pivot(index="year", columns="quarter", values="dev")
    pivot.columns = [f"Q{q}" for q in pivot.columns]
    return pivot


def heatmap(pivot, title, label, cmap="RdBu_r"):
    """Annotated year-by-quarter heatmap centered on zero."""
    limit = max(5.0, float(pivot.abs().max().max()))
    fig, ax = plt.subplots(figsize=(8, max(3, 0.5 * len(pivot) + 1.5)))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap=cmap, center=0,
                vmin=-limit, vmax=limit, linewidths=0.5, linecolor="white",
                ax=ax, cbar_kws={"label": label})
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Quarter")
    ax.set_ylabel("Year")
    ax.tick_params(axis="y", rotation=0)
    fig.tight_layout()
    return fig


def seasonal_chart(d, metric, exclude_covid):
    """Seasonal heatmap for the chosen metric (None if no full years)."""
    pivot = deviation_table(d, METRICS[metric][0], exclude_covid)
    if pivot is None:
        return None
    note = " (Excluding 2020-2021)" if exclude_covid else ""
    title = f"Seasonal {metric.split(' (')[0].title()} Pattern{note}"
    return heatmap(pivot, title,
                   "Deviation from Yearly Quarterly Average (%)")


# ---------- results helpers ----------
def scatter_chart(d):
    """Fare vs. passengers, with COVID quarters highlighted."""
    d = d.dropna(subset=["passengers_millions"])
    if len(d) < 3:
        return None
    covid = d["year"].isin(COVID_YEARS)
    other = d[~covid]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.scatter(other["national_avg_fare"], other["passengers_millions"],
               s=60, color=PAX_COLOR, alpha=0.8, label="Other years")
    ax.scatter(d[covid]["national_avg_fare"],
               d[covid]["passengers_millions"], s=70, color=FARE_COLOR,
               label="2020-2021")
    text = ("All selected years: "
            f"r = {d['national_avg_fare'].corr(d['passengers_millions']):.3f}")
    if len(other) > 2:
        slope, intercept = np.polyfit(other["national_avg_fare"],
                                      other["passengers_millions"], 1)
        xs = np.array([other["national_avg_fare"].min(),
                       other["national_avg_fare"].max()])
        ax.plot(xs, slope * xs + intercept, "k--",
                label="Linear trend (other years)")
        r_other = other["national_avg_fare"].corr(
            other["passengers_millions"])
        text += f"\nOther years: r = {r_other:.3f}"
    ax.text(0.03, 0.96, text, transform=ax.transAxes, va="top",
            bbox=dict(boxstyle="square", facecolor="white", alpha=0.8))
    ax.set_xlabel("Average Domestic Airfare (USD)")
    ax.set_ylabel("Quarterly Passenger Enplanements (Millions)")
    ax.legend(loc="lower right")
    style_axes(ax, "Airfare vs. Passenger Demand: Pandemic vs. Other Years")
    fig.tight_layout()
    return fig


def correlation_table(df):
    """Fare-passenger correlation for five periods (2015-2025 data)."""
    d = df[df["year"] <= 2025].dropna(subset=["passengers_millions"])
    periods = {
        "All Years\n(2015-2025)": d,
        "Excluding\n2020-2021": d[~d["year"].isin(COVID_YEARS)],
        "Pre-COVID\n(2015-2019)": d[d["year"] <= 2019],
        "COVID\n(2020-2021)": d[d["year"].isin(COVID_YEARS)],
        "Post-COVID\n(2022-2025)": d[d["year"] >= 2022],
    }
    return pd.Series({name: p["national_avg_fare"].corr(
        p["passengers_millions"]) for name, p in periods.items()})


def correlation_chart(corr):
    """Bar chart of the correlation for each period."""
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [PAX_COLOR if r >= 0 else FARE_COLOR for r in corr]
    bars = ax.bar(corr.index, corr.values, color=colors, width=0.6)
    for bar, r in zip(bars, corr):
        offset = 0.03 if r >= 0 else -0.03
        ax.text(bar.get_x() + bar.get_width() / 2, r + offset, f"{r:+.3f}",
                ha="center", va="bottom" if r >= 0 else "top",
                fontweight="bold")
    ax.axhline(0, color="black", linewidth=1)
    ax.set_ylim(-0.7, 1.05)
    ax.set_ylabel("Pearson Correlation (r)")
    style_axes(ax, "Airfare-Passenger Demand Correlation by Time Period")
    fig.tight_layout()
    return fig


def yoy_table(df):
    """Year-over-year % change in fare, same quarter, 2016-2025."""
    s = df[df["year"] <= 2025].sort_values("date").copy()
    s["yoy"] = (s["national_avg_fare"] / s["national_avg_fare"].shift(4)
                - 1) * 100
    s = s[s["year"] >= 2016]
    pivot = s.pivot(index="year", columns="quarter", values="yoy")
    pivot.columns = [f"Q{q}" for q in pivot.columns]
    return pivot


# ---------- page sections ----------
def show_overview(df):
    """Title, team, question, data sources and key characteristics."""
    st.title("US Airfare and Passenger Demand")
    st.markdown(f"**Team:** {TEAM}  \n[App code on GitHub]({REPO_URL})")

    st.header("Problem statement")
    st.write(
        "How have airline ticket prices changed over time in the US, and "
        "how are those changes related to passenger demand? Do higher "
        "fares go with fewer passengers, and how do seasonal trends and "
        "major events such as COVID-19 affect airfares?")

    st.header("Data sources")
    st.markdown(
        "- **Average fares:** Bureau of Transportation Statistics (BTS), "
        "Average Domestic Airline Itinerary Fares, one file per quarter.\n"
        "- **Passengers:** BTS Air Carrier Statistics, T-100 Domestic "
        "Market (U.S. carriers), monthly passengers summed into quarters. "
        "Only scheduled passenger service is used.")

    fares, pax = df["national_avg_fare"], df["passengers_millions"]
    st.header("Key characteristics")
    st.markdown(
        f"- **Time span:** {len(df)} quarters of fares "
        f"({df['period'].iloc[0]} to {df['period'].iloc[-1]}); "
        f"{pax.notna().sum()} quarters of passenger data "
        f"(through {df.loc[pax.notna(), 'period'].iloc[-1]}).\n"
        f"- **Average fare:** ${fares.min():,.0f} to ${fares.max():,.0f} "
        f"per quarter (national average, not adjusted for inflation).\n"
        f"- **Passengers:** {pax.min():,.0f} to {pax.max():,.0f} million "
        "domestic passengers per quarter.\n"
        "- **Unit of analysis:** one row per quarter, national level.")


def show_explorer(df):
    """Sidebar controls plus the trend and seasonal charts."""
    st.sidebar.header("Controls")
    st.sidebar.caption("These controls change the charts in the "
                       "'Explore the data' section.")
    years = st.sidebar.slider("Year range", int(df["year"].min()),
                              int(df["year"].max()), (2015, 2025))
    metric = st.sidebar.selectbox("Metric",
                                  ["Both (dual axis)"] + list(METRICS))
    show_covid = st.sidebar.checkbox("Highlight COVID-19 period", value=True)
    exclude_covid = st.sidebar.checkbox(
        "Exclude 2020-2021 from seasonal chart", value=True)
    d = df[(df["year"] >= years[0]) & (df["year"] <= years[1])]
    d = d.reset_index(drop=True)

    st.header("Explore the data")
    st.subheader("Trends over time")
    st.pyplot(trend_chart(d, metric, show_covid))

    st.subheader("Seasonal pattern")
    st.caption("Each cell shows how far a quarter is from its own year's "
               "average, which removes the long-term trend.")
    seasonal_metric = "Average fare ($)" if metric.startswith("Both") \
        else metric
    fig = seasonal_chart(d, seasonal_metric, exclude_covid)
    if fig is None:
        st.info("No complete years in the selected range.")
    else:
        st.pyplot(fig)
        if metric.startswith("Both"):
            st.caption("Showing fares. Choose Passengers in the Metric "
                       "menu to see passenger demand.")
    return d


def show_results(df, d):
    """Written insights and the charts that support them."""
    corr = correlation_table(df)
    all_r, excl_r, pre_r = corr.iloc[0], corr.iloc[1], corr.iloc[2]
    fare_season = deviation_table(df, "national_avg_fare", True).median()
    pax_season = deviation_table(df, "passengers_millions", True).median()
    yoy = yoy_table(df)
    big_q = yoy.stack().idxmax()
    low_q = yoy.stack().idxmin()
    low_fare = df.loc[df["national_avg_fare"].idxmin()]
    low_pax = df.loc[df["passengers_millions"].idxmin()]

    st.header("Results and key insights")
    st.markdown(
        f"- **COVID-19 was the biggest shock.** Fares bottomed out at "
        f"${low_fare['national_avg_fare']:,.0f} in {low_fare['period']} "
        f"and passengers at {low_pax['passengers_millions']:,.0f} million "
        f"in {low_pax['period']}. Fares have since recovered and set new "
        "highs.\n"
        f"- **Fares and passengers look strongly linked, but mostly "
        f"because of COVID.** The correlation is r = {all_r:.2f} across "
        f"all years but only r = {excl_r:.2f} without 2020-2021. Both "
        "measures collapsed together, which is not the same as higher "
        "prices causing fewer passengers.\n"
        f"- **Before COVID the relationship was negative** "
        f"(r = {pre_r:.2f}), as you would expect if higher fares reduce "
        "demand. That period is only 20 quarters and is affected by "
        "seasonality, so we treat it as suggestive, not conclusive.\n"
        f"- **Seasonality is clear.** Relative to their own year, Q1 has "
        f"the fewest passengers ({pax_season['Q1']:+.1f}%) and Q3 has the "
        f"lowest fares ({fare_season['Q3']:+.1f}%), excluding 2020-2021.\n"
        f"- **Fares moved unusually fast in 2020-2022.** The largest "
        f"year-over-year drop was {yoy.stack().min():.1f}% "
        f"(Q{low_q[1][1]} {low_q[0]}) and the largest rise was "
        f"+{yoy.stack().max():.1f}% (Q{big_q[1][1]} {big_q[0]}).")

    st.subheader("Fares vs. passengers")
    st.caption("Uses the year range chosen in the sidebar.")
    fig = scatter_chart(d)
    if fig is None:
        st.info("Select a wider year range to see the scatter plot.")
    else:
        st.pyplot(fig)
    st.subheader("Correlation by time period")
    st.pyplot(correlation_chart(corr))
    st.subheader("Year-over-year change in fares")
    st.pyplot(heatmap(yoy, "Year-over-Year Changes in U.S. Domestic Airfare",
                      "YoY Airfare Change (%)"))
    # Regression results from the team could be added here.


def show_notes():
    """Analysis approach, limitations and ethical considerations."""
    st.header("Analysis approach")
    st.markdown(
        "1. Combined the quarterly fare files into one national series and "
        "summed monthly T-100 passenger counts into quarters.\n"
        "2. Merged the two series by year and quarter.\n"
        "3. Plotted trends, then measured seasonality as each quarter's "
        "percent difference from its own year's average.\n"
        "4. Compared fares and passengers with Pearson correlations for "
        "different periods, separating out the COVID years.\n"
        "5. Looked at year-over-year fare changes to find unusually fast "
        "movements.")

    st.header("Limitations")
    st.markdown(
        "- BTS fares come from a 10% sample of tickets, so they may not "
        "match every fare paid.\n"
        "- National fares are nominal (not adjusted for inflation), so "
        "long-term increases partly reflect rising prices overall.\n"
        "- The data covers domestic travel only, at the national level; "
        "routes, airlines and cabin classes are not separated.\n"
        "- Passengers are counts of boardings, not unique travelers.\n"
        "- Only about 44 quarters are available, and COVID-19 dominates "
        "any statistic that includes 2020-2021.\n"
        "- Correlation does not show cause: fares and demand both rise "
        "in busy seasons and respond to the economy.")

    st.header("Ethical considerations")
    st.markdown(
        "- All data is publicly available government data with no "
        "personal information about travelers.\n"
        "- Sampling bias is possible because only part of all tickets is "
        "included, so results should not be read as exact national "
        "totals.\n"
        "- We avoid claiming that higher prices cause lower demand; the "
        "evidence outside COVID is weak, and overstating it could "
        "mislead readers.\n"
        "- Event markers use documented dates and neutral wording.")


def main():
    """Assemble the page."""
    df = load_data()
    show_overview(df)
    d = show_explorer(df)
    st.divider()
    show_results(df, d)
    st.divider()
    show_notes()


main()