# NADI AI - Setup & Run Instructions

**Developed by Narala Venkatesh, M.Tech Water Resources Engineering, NIT Warangal**

## 1. Folder structure expected

```
NADIAI/
  app.py
  nadi_data_collec.py
  nadi_quality.py
  nadi_statisticaltests.py
  nadi_distfit.py
  nadi_report.py
  nadi_plot.py
  requirements.txt
  DATA/
    camels_ind_name.csv
    camels_ind_land.csv
    camels_ind_topo.csv
    streamflow_observed.csv
```

Your data is already at `C:\Documents\NADIAI\DATA` — `nadi_data_collec.py` is
pre-configured to read from that exact path (see the `DATA_DIR` variable near
the top of `nadi_data_collec.py`). If you ever move the DATA folder, just
update that one line.

> **Why the `nadi_` prefix?** A few generic names like `report`, `plot`, and
> `distfit` are also names of real packages on PyPI. If any of those ever get
> installed in your environment (directly or as a dependency of something
> else), a plain `import report` could silently grab the installed package
> instead of your local file and raise confusing `AttributeError`s. Prefixing
> every local module with `nadi_` makes the import unambiguous no matter what
> else is installed.

## 2. One-time setup (VS Code terminal)

```bash
python -m venv venv
venv\Scripts\activate          # on Windows
pip install -r requirements.txt
```

## 3. Run the app

```bash
streamlit run app.py
```

This opens the app in your browser at `http://localhost:8501`.

## 4. Using the app

1. Pick a station from the dropdown (station names come from `cwc_site_name`
   in `camels_ind_name.csv`).
2. View the station's basic info, data overview, and (if the station has at
   least 10 years with >=50% data availability) quality checks, trend
   analysis, and distribution-fitting results directly in the browser.
3. Click **Generate PDF Report** and then **Download Report (PDF)** to get
   the full technical report.

## 5. What each file does

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI - station picker, inline results, report download |
| `nadi_data_collec.py` | Reads the 4 CSVs, builds AMS/FDC/availability tables for a gauge_id |
| `nadi_quality.py` | IQR + Grubbs-Beck outlier tests, Pettitt + CUSUM change-point tests |
| `nadi_statisticaltests.py` | Mann-Kendall trend test + Sen's slope |
| `nadi_distfit.py` | Fits Normal/Lognormal/Gumbel/GEV/Pearson III/Log-Pearson III (MOM, L-Moments, MLE), GoF tests (KS/Chi2/AD/AIC/RMSE), ranking, quantile estimation |
| `nadi_plot.py` | All matplotlib figures, shared by the Streamlit UI and the PDF report |
| `nadi_report.py` | Assembles the full PDF report (reportlab) |

## 6. Notes on the analysis logic

- A year is "usable" if at least 50% of its calendar days have non-missing
  streamflow data.
- Full statistical analysis (outliers, change-point, trend, distribution
  fitting) only runs if a station has **at least 10 usable years**. Otherwise
  the report/app show a clear message and only the data overview.
- Outlier and change-point/trend tests are run on the **annual maximum
  series (AMS)**, not the raw daily series (standard flood-frequency
  practice, since daily flow is seasonal/non-stationary by nature).
- If `pymannkendall` fails to install for any reason, `nadi_statisticaltests.py`
  automatically falls back to a self-contained Mann-Kendall implementation,
  so the app will still work.

## 7. Troubleshooting

- **"Could not load station list"** — check `DATA_DIR` in `nadi_data_collec.py`
  matches where your 4 CSVs actually live.
- **A specific station shows "insufficient data"** — this is expected
  behaviour per the >=10-usable-years rule above, not a bug.
- **PDF generation is slow** — this is normal; it's building ~15-20 pages
  with 10+ embedded plots. It should complete within a minute.