"""
app.py
NADI AI - Streamlit Application
---------------------------------
Run with:  streamlit run app.py

Simple, blue-themed UI: pick a station from the dropdown, view its basic
details and key plots inline, and download a full technical PDF report.
"""

import os
import streamlit as st

import nadi_data_collec as dc
import nadi_quality as ql
import nadi_statisticaltests as st_tests
import nadi_distfit as dfit
import nadi_plot as pl
import nadi_report as rp

# ---------------------------------------------------------------------------
# PAGE CONFIG + THEME
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NADI AI",
    page_icon="\U0001F4A7",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY_BLUE = "#0B5394"
LIGHT_BLUE = "#3D85C6"

st.markdown(
    f"""
    <style>
    .main {{ background-color: #F5F9FD; }}
    h1, h2, h3 {{ color: {PRIMARY_BLUE}; }}
    div.stButton > button {{
        background-color: {PRIMARY_BLUE};
        color: white;
        border-radius: 6px;
        border: none;
    }}
    div.stButton > button:hover {{
        background-color: {LIGHT_BLUE};
        color: white;
    }}
    .nadi-header {{
        background-color: {PRIMARY_BLUE};
        padding: 18px 24px;
        border-radius: 8px;
        color: white;
        margin-bottom: 18px;
    }}
    .nadi-footer {{
        color: #888888;
        font-size: 0.8rem;
        margin-top: 30px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# CACHED DATA LOADERS
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_stations():
    return dc.load_station_list()


@st.cache_data(show_spinner="Reading station data...")
def cached_station_data(gauge_id):
    return dc.get_station_data(gauge_id)


# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="nadi-header">
        <h1 style="color:white; margin-bottom:0;">NADI AI</h1>
        <p style="margin-top:4px; margin-bottom:0;">
            AI-Assisted Hydrological Frequency Analysis for CAMELS-IND Stations
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "This tool is currently in a developing phase. Thank you for using NADI AI - "
    "your feedback helps us build something better for the hydrology community."
)

# ---------------------------------------------------------------------------
# STATION SELECTION
# ---------------------------------------------------------------------------
try:
    name_df = load_stations()
except Exception as e:
    st.error(f"Could not load station list. Please check that the DATA folder and "
             f"camels_ind_name.csv exist relative to app.py.\n\nError: {e}")
    st.stop()

station_names = sorted(name_df["cwc_site_name"].dropna().unique().tolist())

selected_station = st.selectbox(
    "Select a gauging station",
    options=station_names,
    index=None,
    placeholder="Type or choose a station name...",
)

if not selected_station:
    st.markdown("### Welcome")
    st.write(
        "Select a station from the dropdown above to view its details, streamflow "
        "overview, and generate a full technical flood-frequency analysis report."
    )
    st.stop()

# resolve gauge_id from selected station name (internal only, not displayed)
matched_row = name_df.loc[name_df["cwc_site_name"] == selected_station]
if matched_row.empty:
    st.error("Selected station could not be matched to a gauge_id. Please try another station.")
    st.stop()

gauge_id = matched_row.iloc[0]["gauge_id"]

# ---------------------------------------------------------------------------
# LOAD STATION DATA
# ---------------------------------------------------------------------------
try:
    station_data = cached_station_data(gauge_id)
except Exception as e:
    st.error(f"Error loading data for this station: {e}")
    st.stop()

meta = station_data["meta"]

st.markdown("---")
st.markdown(f"## {meta.get('cwc_site_name', 'N/A')}")

info_col1, info_col2, info_col3 = st.columns(3)
with info_col1:
    st.metric("River Basin", meta.get("river_basin", "N/A"))
with info_col2:
    st.metric("River / Tributary", meta.get("cwc_river", "N/A"))
with info_col3:
    flow_avail = meta.get("flow_availability", None)
    st.metric("Flow Availability (1980-2020)", f"{flow_avail:.1f}%" if flow_avail is not None else "N/A")

for w in station_data["warnings"]:
    st.warning(w)

sufficient = station_data["sufficient_data"]
usable_years = station_data["usable_years"]

st.markdown(
    f"**Usable years (>=50% data availability):** {len(usable_years)} year(s) found."
)

if not sufficient:
    st.error(
        "Sufficient data is not available for this station (minimum 10 usable years "
        "required for full statistical analysis). Only a data overview is shown below."
    )

# ---------------------------------------------------------------------------
# TABS FOR RESULTS PREVIEW
# ---------------------------------------------------------------------------
tab_labels = ["Data Overview"]
if sufficient:
    tab_labels += ["Quality Checks", "Trend Analysis", "Distribution Fitting"]

tabs = st.tabs(tab_labels)

# ---- Tab 1: Data overview ----
with tabs[0]:
    if not station_data["yearly_avail"].empty:
        st.pyplot(pl.plot_yearly_availability(station_data["yearly_avail"]))
    if not station_data["daily_usable"].empty:
        c1, c2 = st.columns(2)
        with c1:
            st.pyplot(pl.plot_monthly_mean_flow(station_data["monthly_mean_flow"]))
        with c2:
            st.pyplot(pl.plot_annual_mean_flow(station_data["annual_mean_flow"]))
        st.pyplot(pl.plot_fdc(station_data["fdc"]))
    if not station_data["ams"].empty:
        st.pyplot(pl.plot_ams_series(station_data["ams"]))
        ams_stats = station_data["basic_stats"]["ams"]
        st.markdown("**Annual Maximum Series - Basic Statistics**")
        st.dataframe(
            {
                "Statistic": ["n (years)", "Mean", "Max", "Min", "Std Dev", "CV", "Skewness"],
                "Value": [
                    ams_stats["n"], round(ams_stats["mean"], 2), round(ams_stats["max"], 2),
                    round(ams_stats["min"], 2), round(ams_stats["std"], 2),
                    round(ams_stats["cv"], 3) if ams_stats["cv"] == ams_stats["cv"] else "N/A",
                    round(ams_stats["skew"], 3) if ams_stats["skew"] == ams_stats["skew"] else "N/A",
                ],
            },
            hide_index=True,
        )
    else:
        st.write("No usable streamflow data available for this station.")

# ---- Remaining tabs only if sufficient data ----
if sufficient:
    ams = station_data["ams"]
    ams_vals = ams["ann_max"].values
    years = ams["year"].values

    with tabs[1]:
        st.markdown("### Outlier Detection")
        iqr_res = ql.iqr_outlier_test(ams_vals)
        st.pyplot(pl.plot_outliers(ams, iqr_res["low_outliers"], iqr_res["high_outliers"], "IQR Test"))
        st.write(f"High outliers: {len(iqr_res['high_outliers'])} | Low outliers: {len(iqr_res['low_outliers'])}")

        gb_res = ql.grubbs_beck_test(ams_vals)
        st.write(f"**Grubbs-Beck:** High outliers: {len(gb_res['high_outliers'])} | "
                 f"Low outliers: {len(gb_res['low_outliers'])} (critical K = {gb_res['K_critical']:.3f})")

        st.markdown("### Change-Point Detection")
        pt_res = ql.pettitt_test(ams_vals, years)
        st.pyplot(pl.plot_pettitt_statistic(years, pt_res.get("U_series", []), pt_res["change_year"]))
        st.pyplot(pl.plot_pettitt_ams(ams, pt_res["change_year"]))
        st.write(f"Pettitt test: change year = {pt_res['change_year']}, "
                 f"p-value = {pt_res['p_value']:.4f}, significant = {pt_res['significant']}")

        cs_res = ql.cusum_test(ams_vals, years)
        st.pyplot(pl.plot_cusum(years, cs_res["cusum"], cs_res["change_year"]))

    with tabs[2]:
        mk_res = st_tests.mann_kendall_test(ams_vals)
        st.pyplot(pl.plot_mann_kendall(ams, mk_res["slope"], mk_res["intercept"], mk_res["trend"]))
        st.write(
            f"**Trend:** {mk_res['trend'].capitalize()} | **p-value:** {mk_res['p']:.4f} | "
            f"**Sen's slope:** {mk_res['slope']:.3f} units/year | "
            f"**Significant (alpha=0.05):** {'Yes' if mk_res['h'] else 'No'}"
        )

    with tabs[3]:
        results = dfit.fit_all_distributions(ams_vals)
        if results.empty:
            st.write("Distribution fitting could not be completed for this station.")
        else:
            st.markdown("**Top 5 Ranked Distribution / Method Combinations**")
            top5 = results.head(5).reset_index(drop=True)
            display_df = top5[["overall_rank", "distribution", "method", "ks_stat",
                                "chi2_stat", "ad_stat", "aic", "rmse"]].copy()
            display_df.columns = ["Rank", "Distribution", "Method", "KS", "Chi2", "AD", "AIC", "RMSE"]
            st.dataframe(display_df, hide_index=True)

            sorted_vals, plotting_pos = dfit.get_plotting_positions(ams_vals)
            curves = dfit.build_distribution_curves(top5, ams_vals)
            st.pyplot(pl.plot_top_distributions(sorted_vals, plotting_pos, curves))

            qtable = dfit.estimate_quantiles(top5)
            labels = [f"{r['distribution']} ({r['method']})" for _, r in top5.iterrows()]
            st.markdown("**Design Discharge Quantiles (m3/s)**")
            st.dataframe(qtable.round(1), hide_index=True)
            st.pyplot(pl.plot_quantile_vs_return_period(qtable, labels))

# ---------------------------------------------------------------------------
# REPORT GENERATION
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("## Download Full Technical Report")
st.write(
    "Generate a complete PDF report including station information, data overview, "
    "outlier and change-point detection, trend analysis, distribution fitting, "
    "goodness-of-fit tests, and design flood magnitudes."
)

if st.button("Generate PDF Report", type="primary"):
    with st.spinner("Generating report... this may take up to a minute."):
        try:
            os.makedirs("generated_reports", exist_ok=True)
            safe_name = "".join(c if c.isalnum() else "_" for c in str(meta.get("cwc_site_name", "station")))
            output_path = os.path.join("generated_reports", f"NADI_AI_Report_{safe_name}.pdf")
            rp.generate_report(station_data, output_path)

            with open(output_path, "rb") as f:
                pdf_bytes = f.read()

            st.success("Report generated successfully!")
            st.download_button(
                label="Download Report (PDF)",
                data=pdf_bytes,
                file_name=f"NADI_AI_Report_{safe_name}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(f"Report generation failed: {e}")
            st.exception(e)

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="nadi-footer">
        NADI AI - developed by Narala Venkatesh, M.Tech Water Resources Engineering, NIT Warangal.<br>
        This tool is in a developing phase. For suggestions, please email
        <b>venkateshnarala387@gmail.com</b>.<br>
        Data source: CAMELS-IND (Mangukiya et al., 2025, Earth Syst. Sci. Data).
    </div>
    """,
    unsafe_allow_html=True,
)