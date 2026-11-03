"""SPOC pipeline retrieval, amplitude periodograms, and optional localization."""
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path

import numpy as np

from .core import CADENCES, arrays, grid_limits


def resolve_target(args):
    if args.tic is not None:
        return str(args.tic), {"input_tic": args.tic}
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astroquery.mast import Catalogs
    center = SkyCoord(args.ra, args.dec, unit="deg", frame="icrs")
    table = Catalogs.query_region(center, radius=args.radius*u.arcsec, catalog="TIC")
    if not len(table):
        raise ValueError("No TIC counterpart within the coordinate radius")
    distances = center.separation(SkyCoord(table["ra"], table["dec"], unit="deg")).arcsec
    keep = np.isfinite(distances) & (distances <= args.radius)
    table, distances = table[keep], distances[keep]
    ids = set(str(row["ID"]) for row in table)
    if len(ids) != 1:
        listing = ", ".join(f"TIC {r['ID']} ({d:.2f} arcsec)" for r,d in zip(table,distances))
        raise ValueError("No unique TIC match: review candidates and rerun with --tic. " + listing)
    tic = ids.pop()
    return tic, {"input_ra_deg":args.ra, "input_dec_deg":args.dec,
                 "radius_arcsec":args.radius, "tic":tic,
                 "separation_arcsec":float(np.min(distances))}


def prepare(lc, sigma=None, flatten_window=None):
    _, _, _, idx = arrays(lc.time.value, lc.flux.value, lc.flux_err.value)
    clean = lc[idx].copy()
    if sigma is not None:
        clean = clean.remove_outliers(sigma=sigma)
    if flatten_window is not None:
        if flatten_window < 5 or flatten_window % 2 == 0 or flatten_window >= len(clean):
            raise ValueError("Flatten window must be odd, >=5, and shorter than the series")
        clean = clean.flatten(window_length=flatten_window)
    median = np.median(clean.flux.value)
    if not np.isfinite(median) or median <= 0:
        raise ValueError("A positive median flux is required for normalization")
    clean = clean.normalize(unit="ppt")
    clean.flux = clean.flux - 1000 * clean.flux.unit
    arrays(clean.time.value, clean.flux.value, clean.flux_err.value)
    return clean


def analyze(lc, prefix, cadence, args):
    import astropy.units as u
    import matplotlib.pyplot as plt
    t,y,e,_ = arrays(lc.time.value, lc.flux.value, lc.flux_err.value)
    lo,hi,nyquist,bins = grid_limits(t,cadence,args.fmin,args.fmax,args.oversample,
                                    args.max_bins,args.super_nyquist)
    pg = lc.to_periodogram(method="lombscargle", minimum_frequency=lo*u.uHz,
                           maximum_frequency=hi*u.uHz, freq_unit=u.uHz,
                           normalization="amplitude", oversample_factor=args.oversample,
                           ls_method="fast")
    frequency = pg.frequency.to_value(u.uHz)
    amplitude = pg.power.value
    if not len(frequency) or not np.all(np.isfinite(amplitude)):
        raise ValueError("Invalid amplitude periodogram; inspect flux variability and grid")
    np.savetxt(str(prefix)+"_lc.csv", np.c_[lc.time.tdb.jd,y,e],delimiter=",",
               header="bjd_tdb,delta_flux_ppt,flux_err_ppt",comments="")
    np.savetxt(str(prefix)+"_lsp.csv", np.c_[frequency,frequency*0.0864,amplitude],delimiter=",",
               header="frequency_uhz,frequency_cpd,amplitude_ppt",comments="")
    fig,axes = plt.subplots(2,1,figsize=(11,7))
    axes[0].plot(lc.time.tdb.jd-2457000,y,".",ms=1,color="0.25")
    axes[0].set(xlabel="BJD_TDB - 2457000 (d)",ylabel="Relative flux (ppt)")
    axes[1].plot(frequency,amplitude,color="navy",lw=0.65)
    axes[1].set(xlabel=r"Frequency ($\mu$Hz)",ylabel="LS amplitude (ppt)",xlim=(lo,hi))
    fig.tight_layout(); fig.savefig(str(prefix)+"_diagnostics.png",dpi=200); plt.close(fig)
    return {"n_points":len(t), "baseline_day":float(np.ptp(t)), "fmin_uhz":lo,
            "fmax_uhz":hi, "nominal_nyquist_uhz":nyquist, "n_frequencies":len(frequency),
            "estimated_bins":bins, "time_export":"BJD_TDB", "flux_unit":"ppt",
            "lsp":"Lightkurve amplitude normalization; unweighted"}


def localize(tic, sector, cadence, prefix, args):
    import lightkurve as lk
    import astropy.units as u
    import matplotlib.pyplot as plt
    try:
        import TESS_Localize as tl
    except ImportError as exc:
        raise RuntimeError('Install localization: python -m pip install ".[localize]"') from exc
    search = lk.search_targetpixelfile(f"TIC {tic}",mission="TESS",author="SPOC",
                                      sector=sector,exptime=cadence)
    search.table.write(str(prefix)+"_tpf_search.ecsv",format="ascii.ecsv",overwrite=True)
    if len(search) != 1:
        raise ValueError(f"Expected one matching TPF, found {len(search)}; inspect the search table")
    tpf = search[0].download(quality_bitmask=args.quality,download_dir=args.cache)
    if tpf is None:
        raise RuntimeError("TPF download returned no data")
    target_id = tpf.meta.get("TICID")
    if target_id is None or int(target_id) != int(tic) or int(tpf.meta["SECTOR"]) != sector:
        raise ValueError("TPF target/sector metadata do not match requested target")
    plt.close("all")
    try:
        with open(str(prefix)+"_localize.txt","w") as log, redirect_stdout(log), redirect_stderr(log):
            obj = tl.Localize(targetpixelfile=tpf,gaia=True,magnitude_limit=args.magnitude_limit,
                              frequencies=args.frequencies,frequnit=u.uHz,
                              principal_components=args.pca)
            obj.info()
            obj.pca()
            obj.plot(frequencylist_index=0,method="snr")
            for number in plt.get_fignums():
                plt.figure(number).savefig(str(prefix)+f"_localize_{number}.png",
                                           dpi=180,bbox_inches="tight")
    finally:
        plt.close("all")


def run(args):
    import lightkurve as lk
    tic,resolved = resolve_target(args)
    out = Path(args.output)/f"TIC_{tic}"; out.mkdir(parents=True,exist_ok=True)
    manifest = {"started_utc":datetime.now(timezone.utc).isoformat(),"tic":tic,
                "target":resolved,"arguments":vars(args),"versions":{},"products":[],
                "inventories":[],"errors":[]}
    for name in ["lc-tess-compact","numpy","astropy","lightkurve","tess-localize"]:
        try:manifest["versions"][name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:pass
    successes = 0
    try:
        for cadence in CADENCES[args.cadence]:
            search = lk.search_lightcurve(f"TIC {tic}",mission="TESS",author="SPOC",
                                         exptime=cadence,sector=args.sectors)
            manifest["inventories"].append({"cadence_s":cadence,"n_products":len(search)})
            if len(search):
                search.table.write(out/f"search_{cadence}s.ecsv",format="ascii.ecsv",overwrite=True)
            print(f"{cadence}s: {len(search)} SPOC products")
            print(search)
            if args.search_only:continue
            curves=[];seen=set()
            for i in range(len(search)):
                row={str(k):str(search.table[i][k]) for k in search.table.colnames}
                try:
                    lc=search[i].download(flux_column=args.flux,quality_bitmask=args.quality,
                                          download_dir=args.cache)
                    if lc is None:raise RuntimeError("Download returned no data")
                    if lc.meta.get("TICID") is None or int(lc.meta["TICID"]) != int(tic):
                        raise ValueError("Downloaded TIC metadata differ from request or are missing")
                    sector=int(lc.meta["SECTOR"])
                    if sector in seen:
                        raise ValueError("Duplicate sector/cadence product: review recorded search table")
                    seen.add(sector)
                    prefix=out/f"TIC_{tic}_s{sector:04d}_{cadence}s"
                    clean=prepare(lc,args.sigma,args.flatten_window)
                    stats=analyze(clean,prefix,cadence,args)
                    stats.update({"sector":sector,"cadence_s":cadence,"search_row":row,
                                  "flux_column":args.flux,"crowdsap":str(lc.meta.get("CROWDSAP","unknown"))})
                    manifest["products"].append(stats);curves.append(clean);successes+=1
                    if args.frequencies:
                        try:localize(tic,sector,cadence,prefix,args)
                        except Exception as exc:
                            manifest["errors"].append({"stage":"localize","sector":sector,
                                                       "cadence_s":cadence,"error":str(exc)})
                            print(f"Localization failed: {exc}")
                except Exception as exc:
                    manifest["errors"].append({"stage":"lightcurve","cadence_s":cadence,
                                               "search_row":row,"error":str(exc)})
                    print(f"Product failed: {exc}")
            if args.stitch and len(curves)>1:
                try:
                    combined=lk.LightCurveCollection(curves).stitch(corrector_func=lambda lc:lc)
                    combined=combined[np.argsort(combined.time.value)]
                    stats=analyze(combined,out/f"TIC_{tic}_stitched_{cadence}s",cadence,args)
                    stats.update({"sector":"stitched","cadence_s":cadence})
                    manifest["products"].append(stats)
                except Exception as exc:
                    manifest["errors"].append({"stage":"stitch","cadence_s":cadence,"error":str(exc)})
    except Exception as exc:
        manifest["errors"].append({"stage":"archive_search","error":str(exc)})
        raise
    finally:
        manifest["finished_utc"]=datetime.now(timezone.utc).isoformat()
        (out/"manifest.json").write_text(json.dumps(manifest,indent=2,default=str))
    if not args.search_only and not successes:
        raise RuntimeError("No light curves processed: consult inventories and manifest")
    if manifest["errors"]:
        print("Partial success; inspect manifest.json")
        return 2
    return 0
