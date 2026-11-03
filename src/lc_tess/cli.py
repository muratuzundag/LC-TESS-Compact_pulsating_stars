"""User-facing command-line interface."""
import argparse
import math

from . import __version__


def parser():
    p=argparse.ArgumentParser(description="LC TESS Compact pulsating stars: SPOC USC/SC photometry")
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--tic",type=int)
    group.add_argument("--ra",type=float,help="ICRS right ascension, decimal degrees")
    p.add_argument("--dec",type=float,help="ICRS declination, decimal degrees")
    p.add_argument("--radius",type=float,default=5.,help="TIC matching radius, arcsec")
    p.add_argument("--cadence",choices=["usc","sc","both"],default="both")
    p.add_argument("--sectors",nargs="+",type=int)
    p.add_argument("--flux",choices=["pdcsap_flux","sap_flux"],default="pdcsap_flux")
    p.add_argument("--quality",choices=["default","hard","hardest","none"],default="default")
    p.add_argument("--sigma",type=float,help="Optional outlier clipping, default off")
    p.add_argument("--flatten-window",type=int,help="Odd length in cadences; default off")
    p.add_argument("--fmin",type=float,help="Microhertz; default 1/baseline")
    p.add_argument("--fmax",type=float,help="Microhertz; default 0.99*nominal cadence Nyquist")
    p.add_argument("--oversample",type=int,default=5)
    p.add_argument("--max-bins",type=int,default=2000000)
    p.add_argument("--super-nyquist",action="store_true")
    p.add_argument("--stitch",action="store_true")
    p.add_argument("--search-only",action="store_true")
    p.add_argument("--frequencies",nargs="+",type=float,help="Same-source localization frequencies in microhertz")
    p.add_argument("--pca",type=int,default=3)
    p.add_argument("--magnitude-limit",type=float,default=18.)
    p.add_argument("--output",default="results")
    p.add_argument("--cache",default=".cache/lightkurve")
    p.add_argument("--version",action="version",version=__version__)
    return p


def main(argv=None):
    p=parser();a=p.parse_args(argv)
    if (a.ra is None)!=(a.dec is None):p.error("Supply --ra and --dec together, or --tic alone")
    if a.tic is not None and a.tic<=0:p.error("TIC must be positive")
    if a.ra is not None and not (math.isfinite(a.ra) and math.isfinite(a.dec)
                                 and 0<=a.ra<360 and -90<=a.dec<=90):
        p.error("Invalid ICRS coordinates")
    for name in ["radius","sigma","fmin","fmax"]:
        value=getattr(a,name)
        if value is not None and (not math.isfinite(value) or value<=0):p.error(f"{name} must be positive and finite")
    if a.fmin is not None and a.fmax is not None and a.fmin>=a.fmax:p.error("fmin must be below fmax")
    if a.oversample<1 or a.max_bins<2 or a.pca<0:p.error("Invalid grid or PCA setting")
    if a.sectors and any(s<1 for s in a.sectors):p.error("Sector numbers must be positive")
    if a.flatten_window is not None and (a.flatten_window<5 or a.flatten_window%2==0):
        p.error("Flatten window must be odd and >=5")
    if not math.isfinite(a.magnitude_limit):p.error("Magnitude limit must be finite")
    if a.frequencies and any(not math.isfinite(f) or f<=0 for f in a.frequencies):
        p.error("Localization frequencies must be positive finite microhertz values")
    try:
        from .workflow import run
        return run(a)
    except Exception as exc:
        print(f"LC-TESS failed: {exc}")
        return 1
