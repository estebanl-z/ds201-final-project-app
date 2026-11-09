# US Airfare and Passenger Demand: Streamlit App

**Team:** Luke and Angelina

- **Live app:** https://ds201-final-project-app-iszpc8tvrdd8wrl6pdm2bl.streamlit.app/
- **Data and analysis repository:** https://github.com/Angelina181399/ds201-final-project-data-analysis

This repository holds the code for an interactive dashboard that explores how
US domestic airfares changed from 2015 to 2026 and how they relate to
passenger demand, including seasonal patterns and the effect of COVID-19.

## Key features

- **Interactive controls (sidebar):** choose a year range, switch the metric
  (average fare, passengers, or both on a dual axis), highlight the COVID-19
  period, and exclude 2020-2021 from the seasonal chart.
- **Trend chart:** quarterly fares and/or passengers, with a labeled COVID-19
  band.
- **Seasonal heatmap:** each quarter's percent difference from its own year's
  average, which removes the long-term trend.
- **Results section:** a written summary of key insights, a fare vs. passenger
  scatter plot (COVID quarters highlighted), correlations for five time
  periods, and a year-over-year fare change heatmap.
- **Project documentation inside the app:** problem statement, data sources,
  key characteristics, analysis approach, limitations, and ethical
  considerations.

## Repository structure

```
ds201-final-project-app/
  app/
    app.py                          Streamlit app (all dashboard code)
  data/
    merged_fare_passengers.csv      quarterly fares and passengers used by the app
  requirements.txt                  Python packages needed to run the app
  README.md
```

The code that cleans and merges the raw data lives in the separate analysis
repository (linked above). This repository only contains the final merged
file the app reads.

## Data

`data/merged_fare_passengers.csv` has one row per quarter:

| Column | Meaning |
|---|---|
| `period` | Label such as `2015-Q1` |
| `year`, `quarter` | Calendar year and quarter (1-4) |
| `national_avg_fare` | National average domestic fare in USD (BTS, not inflation-adjusted) |
| `passengers` | Total scheduled domestic passengers (BTS T-100) |
| `passengers_millions` | Same, in millions |

Passenger data ends in Q4 2025, so Q1 and Q2 of 2026 have blank passenger
values.

## Run the app locally

```
git clone https://github.com/estebanl-z/ds201-final-project-app
cd ds201-final-project-app
python -m pip install -r requirements.txt
python -m streamlit run app/app.py
```

Streamlit prints a local link (usually `http://localhost:8501`) to open in a
browser.

## Data sources

- Bureau of Transportation Statistics (BTS), Average Domestic Airline
  Itinerary Fares: <https://www.transtats.bts.gov/AverageFare/>
- BTS Air Carrier Statistics, T-100 Domestic Market (U.S. carriers):
  <https://www.transtats.bts.gov/>