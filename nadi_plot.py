"""
plot.py
NADI AI - Plotting Module
--------------------------
All matplotlib figures used across the app and the PDF report live here.
Every function returns a matplotlib Figure object (never calls plt.show()),
so the same figure can be st.pyplot()'d in Streamlit and also saved as a
PNG for embedding into the PDF report.

Colour scheme kept consistent with the blue NADI AI theme.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- NADI AI colour palette ----
PRIMARY_BLUE = "#0B5394"
LIGHT_BLUE = "#3D85C6"
ACCENT_BLUE = "#9FC5E8"
GRID_GREY = "#D9D9D9"
DANGER_RED = "#CC4125"

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _style_axes(ax):
    ax.grid(True, linestyle="--", linewidth=0.5, color=GRID_GREY, alpha=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def plot_yearly_availability(yearly_avail, min_pct_threshold=50.0):
    """Bar chart of annual % data availability with the usability threshold line."""
    fig, ax = plt.subplots(figsize=(9, 4))
    if yearly_avail.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        return fig
    colors = [PRIMARY_BLUE if p >= min_pct_threshold else ACCENT_BLUE
              for p in yearly_avail["pct_available"]]
    ax.bar(yearly_avail["year"], yearly_avail["pct_available"], color=colors, width=0.8)
    ax.axhline(min_pct_threshold, color=DANGER_RED, linestyle="--", linewidth=1,
               label=f"{min_pct_threshold:.0f}% usability threshold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Data availability (%)")
    ax.set_title("Annual Data Availability")
    ax.set_ylim(0, 105)
    ax.legend(loc="lower right", fontsize=8)
    _style_axes(ax)
    fig.tight_layout()
    return fig


def plot_monthly_mean_flow(monthly_mean_flow):
    """Bar chart of long-term mean monthly flow (climatology)."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(range(1, 13), monthly_mean_flow.values, color=LIGHT_BLUE)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_xlabel("Month")
    ax.set_ylabel("Mean flow (m3/s)")
    ax.set_title("Mean Monthly Flow")
    _style_axes(ax)
    fig.tight_layout()
    return fig


def plot_annual_mean_flow(annual_mean_flow):
    """Line + marker plot of annual mean flow across usable years."""
    fig, ax = plt.subplots(figsize=(9, 4))
    if annual_mean_flow.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        return fig
    ax.plot(annual_mean_flow["year"], annual_mean_flow["mean_flow"],
            marker="o", markersize=3, color=PRIMARY_BLUE, linewidth=1.2)
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean annual flow (m3/s)")
    ax.set_title("Mean Annual Flow (usable years)")
    _style_axes(ax)
    fig.tight_layout()
    return fig


def plot_fdc(fdc):
    """Flow duration curve - discharge vs exceedance probability, normal (linear) scale."""
    fig, ax = plt.subplots(figsize=(7.5, 5))
    if fdc.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        return fig
    ax.plot(fdc["exceedance_prob"], fdc["flow"], color=PRIMARY_BLUE, linewidth=1.5)
    ax.set_xlabel("Exceedance probability (%)")
    ax.set_ylabel("Discharge (m3/s)")
    ax.set_title("Flow Duration Curve")
    ax.set_xlim(0, 100)
    ax.set_ylim(bottom=0)
    _style_axes(ax)
    fig.tight_layout()
    return fig


def plot_ams_series(ams):
    """Annual maximum series plot."""
    fig, ax = plt.subplots(figsize=(9, 4))
    if ams.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        return fig
    ax.plot(ams["year"], ams["ann_max"], marker="o", markersize=4,
            color=PRIMARY_BLUE, linewidth=1.3)
    ax.axhline(ams["ann_max"].mean(), color=DANGER_RED, linestyle="--",
               linewidth=1, label="Mean")
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual maximum discharge (m3/s)")
    ax.set_title("Annual Maximum Series (AMS)")
    ax.legend(fontsize=8)
    _style_axes(ax)
    fig.tight_layout()
    return fig


def plot_outliers(ams, low_outliers, high_outliers, method_name=""):
    """AMS scatter with high/low outliers highlighted."""
    fig, ax = plt.subplots(figsize=(9, 4))
    if ams.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        return fig
    ax.plot(ams["year"], ams["ann_max"], marker="o", markersize=4,
            color=PRIMARY_BLUE, linewidth=1, label="Annual maximum", zorder=1)

    if len(high_outliers) > 0:
        mask = ams["ann_max"].isin(high_outliers)
        ax.scatter(ams.loc[mask, "year"], ams.loc[mask, "ann_max"],
                    color=DANGER_RED, s=70, zorder=3, label="High outlier", marker="^")
    if len(low_outliers) > 0:
        mask = ams["ann_max"].isin(low_outliers)
        ax.scatter(ams.loc[mask, "year"], ams.loc[mask, "ann_max"],
                    color="#E69138", s=70, zorder=3, label="Low outlier", marker="v")

    ax.set_xlabel("Year")
    ax.set_ylabel("Annual maximum discharge (m3/s)")
    ax.set_title(f"Outlier Detection - {method_name}")
    ax.legend(fontsize=8)
    _style_axes(ax)
    fig.tight_layout()
    return fig


def plot_pettitt_statistic(years, U_series, change_year=None):
    """Pettitt test statistic (U_t) vs. year."""
    fig, ax = plt.subplots(figsize=(9, 4))
    if len(years) == 0 or len(U_series) == 0:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        return fig
    ax.plot(years, U_series, marker="o", markersize=3, color=PRIMARY_BLUE, linewidth=1.2)
    ax.axhline(0, color="black", linewidth=0.8)
    if change_year is not None:
        ax.axvline(change_year, color=DANGER_RED, linestyle="--", linewidth=1.3,
                   label=f"Change point ({change_year})")
        ax.legend(fontsize=8)
    ax.set_xlabel("Year")
    ax.set_ylabel("Pettitt statistic (U_t)")
    ax.set_title("Pettitt Test Statistic vs. Year")
    _style_axes(ax)
    fig.tight_layout()
    return fig


def plot_pettitt_ams(ams, change_year):
    """AMS series with Pettitt change point marked and before/after means."""
    fig, ax = plt.subplots(figsize=(9, 4))
    if ams.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        return fig
    ax.plot(ams["year"], ams["ann_max"], marker="o", markersize=4,
            color=PRIMARY_BLUE, linewidth=1.2, label="Annual maximum")

    if change_year is not None:
        ax.axvline(change_year, color=DANGER_RED, linestyle="--", linewidth=1.3,
                   label=f"Change point ({change_year})")
        before = ams.loc[ams["year"] <= change_year, "ann_max"]
        after = ams.loc[ams["year"] > change_year, "ann_max"]
        if len(before) > 0:
            ax.hlines(before.mean(), ams["year"].min(), change_year,
                      color="#38761D", linewidth=2, label="Mean before")
        if len(after) > 0:
            ax.hlines(after.mean(), change_year, ams["year"].max(),
                      color="#E69138", linewidth=2, label="Mean after")

    ax.set_xlabel("Year")
    ax.set_ylabel("Annual maximum discharge (m3/s)")
    ax.set_title("Annual Maximum Series with Change Point")
    ax.legend(fontsize=8)
    _style_axes(ax)
    fig.tight_layout()
    return fig


def plot_cusum(years, cusum_values, change_year=None):
    """CUSUM test statistic vs. year."""
    fig, ax = plt.subplots(figsize=(9, 4))
    if len(years) == 0:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        return fig
    ax.plot(years, cusum_values, marker="o", markersize=3, color=PRIMARY_BLUE, linewidth=1.2)
    ax.axhline(0, color="black", linewidth=0.8)
    if change_year is not None:
        ax.axvline(change_year, color=DANGER_RED, linestyle="--", linewidth=1.3,
                   label=f"Change point ({change_year})")
        ax.legend(fontsize=8)
    ax.set_xlabel("Year")
    ax.set_ylabel("CUSUM statistic")
    ax.set_title("CUSUM Test Statistic vs. Year")
    _style_axes(ax)
    fig.tight_layout()
    return fig


def plot_mann_kendall(ams, sen_slope, sen_intercept, trend_label=""):
    """AMS series with Sen's slope trend line overlaid."""
    fig, ax = plt.subplots(figsize=(9, 4))
    if ams.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        return fig
    ax.plot(ams["year"], ams["ann_max"], marker="o", markersize=4,
            color=PRIMARY_BLUE, linewidth=1, label="Annual maximum")

    years = ams["year"].values
    trend_line = sen_intercept + sen_slope * (years - years[0])
    ax.plot(years, trend_line, color=DANGER_RED, linewidth=1.8,
            label=f"Sen's slope trend ({trend_label})")

    ax.set_xlabel("Year")
    ax.set_ylabel("Annual maximum discharge (m3/s)")
    ax.set_title("Mann-Kendall Trend Test")
    ax.legend(fontsize=8)
    _style_axes(ax)
    fig.tight_layout()
    return fig


def plot_top_distributions(ams_sorted, plotting_positions, dist_curves, top_n=5):
    """
    Overlay top-N fitted distribution CDFs (as quantile vs non-exceedance prob)
    against the plotting-position points of observed AMS.

    dist_curves: list of dicts with keys 'label', 'x' (probability), 'y' (magnitude)
    """
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(plotting_positions, ams_sorted, color="black", s=25, zorder=5,
               label="Observed AMS (plotting position)")

    colors = [PRIMARY_BLUE, "#38761D", "#E69138", "#674EA7", DANGER_RED]
    for i, curve in enumerate(dist_curves[:top_n]):
        ax.plot(curve["x"], curve["y"], linewidth=1.6,
                color=colors[i % len(colors)], label=curve["label"])

    ax.set_xlabel("Non-exceedance probability")
    ax.set_ylabel("Discharge (m3/s)")
    ax.set_title("Top Fitted Distributions vs. Observed Annual Maxima")
    ax.legend(fontsize=7.5, loc="upper left")
    _style_axes(ax)
    fig.tight_layout()
    return fig


def plot_quantile_vs_return_period(quantile_table, dist_labels):
    """
    Plot magnitude vs return period (normal/linear scale) for the top distributions.
    quantile_table: DataFrame with 'return_period' column and one column per dist_label
    """
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    colors = [PRIMARY_BLUE, "#38761D", "#E69138", "#674EA7", DANGER_RED]
    for i, label in enumerate(dist_labels):
        if label in quantile_table.columns:
            ax.plot(quantile_table["return_period"], quantile_table[label],
                    marker="o", markersize=4, linewidth=1.4,
                    color=colors[i % len(colors)], label=label)
    ax.set_xlabel("Return period (years)")
    ax.set_ylabel("Design discharge (m3/s)")
    ax.set_title("Design Flood Magnitude vs. Return Period")
    ax.set_xticks(quantile_table["return_period"])
    ax.legend(fontsize=8)
    _style_axes(ax)
    fig.tight_layout()
    return fig


def plot_best_fit_quantiles(quantile_table, best_label):
    """Standalone plot of the single best-fit distribution's quantile curve (normal/linear scale)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    if best_label in quantile_table.columns:
        ax.plot(quantile_table["return_period"], quantile_table[best_label],
                marker="o", markersize=5, linewidth=1.8, color=PRIMARY_BLUE)
    ax.set_xlabel("Return period (years)")
    ax.set_ylabel("Design discharge (m3/s)")
    ax.set_title(f"Best-Fit Distribution: {best_label}")
    ax.set_xticks(quantile_table["return_period"])
    _style_axes(ax)
    fig.tight_layout()
    return fig


def save_fig(fig, path, dpi=150):
    """Save a figure to disk (used by report.py before embedding into PDF)."""
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return path