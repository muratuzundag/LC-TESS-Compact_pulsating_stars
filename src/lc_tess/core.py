"""Validated time-series and sampling helpers; no archive access."""
import numpy as np

CADENCES = {"usc": (20,), "sc": (120,), "both": (20, 120)}

def arrays(time, flux, error):
    t, y, e = [np.asarray(a, dtype=float) for a in (time, flux, error)]
    if not (t.ndim == y.ndim == e.ndim == 1 and len(t) == len(y) == len(e)):
        raise ValueError("Time, flux and error must be equal-length 1-D arrays")
    good = np.isfinite(t) & np.isfinite(y) & np.isfinite(e) & (e > 0)
    idx = np.flatnonzero(good)
    idx = idx[np.argsort(t[idx])]
    if len(idx) < 10 or np.any(np.diff(t[idx]) <= 0):
        raise ValueError("Need at least 10 valid samples with unique, increasing times")
    return t[idx], y[idx], e[idx], idx


def grid_limits(time_day, cadence, lower=None, upper=None, oversample=5,
                max_bins=2_000_000, super_nyquist=False):
    baseline = float(np.ptp(time_day)) * 86400
    if baseline <= 0 or not np.isfinite(baseline):
        raise ValueError("Invalid time baseline")
    if oversample < 1 or max_bins < 2:
        raise ValueError("Invalid oversampling or frequency-bin limit")
    nyquist = 1e6 / (2 * cadence)
    lo = 1e6 / baseline if lower is None else lower
    hi = 0.99 * nyquist if upper is None else upper
    if not (np.isfinite(lo) and np.isfinite(hi) and 0 < lo < hi):
        raise ValueError("Require finite 0 < fmin < fmax, in microhertz")
    if hi > nyquist and not super_nyquist:
        raise ValueError("Above nominal cadence Nyquist; use --super-nyquist explicitly")
    bins = int(np.ceil((hi-lo) * 1e-6 * baseline * oversample)) + 1
    if bins > max_bins:
        raise ValueError(f"About {bins:,} frequency bins required; narrow range or increase --max-bins")
    if bins < 2:
        raise ValueError("Frequency range is too narrow")
    return float(lo), float(hi), float(nyquist), bins
