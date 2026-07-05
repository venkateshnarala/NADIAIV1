"""
statisticaltests.py
NADI AI - Trend Analysis Module
---------------------------------
Mann-Kendall trend test + Sen's slope estimator, applied to the annual
maximum series (AMS).

Uses the `pymannkendall` package if available (installed via
requirements.txt); falls back to a self-contained implementation otherwise
so the app never crashes purely due to a missing optional dependency.
"""

import numpy as np
from scipy import stats

try:
    import pymannkendall as mk
    _HAS_PYMK = True
except ImportError:
    _HAS_PYMK = False


def _manual_mann_kendall(x, alpha=0.05):
    """Self-contained Mann-Kendall + Sen's slope (used if pymannkendall is unavailable)."""
    x = np.asarray(x, dtype=float)
    n = len(x)

    # S statistic
    s = 0
    for i in range(n - 1):
        s += np.sum(np.sign(x[i + 1:] - x[i]))

    # variance (no tie correction for simplicity - adequate for annual max series)
    unique_vals, counts = np.unique(x, return_counts=True)
    tie_term = np.sum(counts * (counts - 1) * (2 * counts + 5))
    var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0

    if s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0.0

    p = 2 * (1 - stats.norm.cdf(abs(z)))
    h = p < alpha

    if z > 0 and h:
        trend = "increasing"
    elif z < 0 and h:
        trend = "decreasing"
    else:
        trend = "no trend"

    tau = s / (0.5 * n * (n - 1))

    # Sen's slope: median of all pairwise slopes
    slopes = []
    for i in range(n - 1):
        for j in range(i + 1, n):
            slopes.append((x[j] - x[i]) / (j - i))
    slope = np.median(slopes)
    intercept = np.median(x) - slope * np.median(np.arange(n))

    return dict(trend=trend, h=bool(h), p=float(p), z=float(z), Tau=float(tau),
                s=int(s), var_s=float(var_s), slope=float(slope), intercept=float(intercept))


def mann_kendall_test(ams_values, alpha=0.05):
    """
    Run the Mann-Kendall trend test and Sen's slope estimator on the AMS.

    Returns dict: trend, h (significant?), p, z, Tau, s, var_s, slope, intercept
    """
    ams_values = np.asarray(ams_values, dtype=float)
    ams_values = ams_values[~np.isnan(ams_values)]

    if len(ams_values) < 4:
        return dict(trend="insufficient data", h=False, p=np.nan, z=np.nan,
                    Tau=np.nan, s=np.nan, var_s=np.nan, slope=np.nan, intercept=np.nan)

    if _HAS_PYMK:
        result = mk.original_test(ams_values, alpha=alpha)
        return dict(
            trend=result.trend, h=bool(result.h), p=float(result.p), z=float(result.z),
            Tau=float(result.Tau), s=float(result.s), var_s=float(result.var_s),
            slope=float(result.slope), intercept=float(result.intercept)
        )
    else:
        return _manual_mann_kendall(ams_values, alpha=alpha)


# ---------------------------------------------------------------------------
# Reference text block reused in report.py
# ---------------------------------------------------------------------------
MANN_KENDALL_DESCRIPTION = {
    "title": "Mann-Kendall Trend Test",
    "definition": (
        "The Mann-Kendall (MK) Test is a non-parametric statistical test "
        "used to determine whether a time series shows a consistent "
        "increasing or decreasing trend over time. Since it is based on the "
        "relative order of observations rather than their actual values, it "
        "does not require the data to follow any specific probability "
        "distribution. To quantify the magnitude of the detected trend, the "
        "Sen's Slope Estimator is used, which provides a robust estimate of "
        "the average rate of change per year."
    ),
    "purpose": (
        "The test is commonly performed at a 5% significance level "
        "(alpha = 0.05). A p-value less than 0.05 indicates a statistically "
        "significant trend. The Kendall's Tau (tau) value describes the "
        "direction and strength of the trend, ranging from -1 (strong "
        "decreasing trend) to +1 (strong increasing trend), while Sen's "
        "slope indicates the estimated rate of change in discharge per year."
    ),
    "formula_lines": [
        "S  =  sum ( i = 1 to n-1 )  sum ( j = i+1 to n )   sgn(x_j - x_i)",
        "sgn(x_j - x_i) =  +1  if x_j > x_i  ;   0  if x_j = x_i  ;   -1  if x_j < x_i",
        "Z  =  (S - 1) / sqrt(Var(S))   if S > 0",
        "Z  =  0                        if S = 0",
        "Z  =  (S + 1) / sqrt(Var(S))   if S < 0",
        "Sen's slope (beta)  =  median { (x_j - x_i) / (j - i) }   for all i < j",
    ],
    "standard_values": "Significance level alpha = 0.05 (95% confidence)",
    "parameter_explanation": (
        "Tau: Kendall's rank correlation coefficient (-1 to +1); "
        "p-value: probability the observed trend arose by chance (trend deemed "
        "significant if p < alpha); "
        "Sen's slope: robust estimate of the rate of change per year (units/year)."
    ),
}