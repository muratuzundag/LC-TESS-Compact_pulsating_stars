# LC TESS Compact pulsating stars

![LC TESS Compact pulsating stars banner](assets/LC_TESS_banner.png)

A Python workflow for retrieving TESS SPOC light curves, computing Lomb–Scargle amplitude spectra, and optionally localizing selected variability in target-pixel data.

Designed for compact-star asteroseismology, including studies of pulsating white dwarfs and hot subdwarfs. Users provide a TIC identifier or sky coordinates; the workflow selects available short-cadence data and produces reproducible data products and diagnostic figures.

> **Release status:** Version 0.1.0 is a release candidate. Source syntax and dependency-light tests have been checked. Live MAST downloads, a full runtime installation, and actual TESS-Localize execution have **not** been validated in the generation environment. Complete [VALIDATION.md](VALIDATION.md) before advertising a stable scientific release.

| Name | Value |
|---|---|
| Repository | `LC-TESS-Compact-Pulsating-Stars` |
| Python distribution | `lc-tess-compact` |
| Importable module | `lc_tess` |
| Terminal command | `lc-tess` |
| USC | 20-second cadence |
| SC | 120-second cadence |

## Contents

- [Capabilities and scope](#capabilities-and-scope)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Coordinates and target matching](#coordinates-and-target-matching)
- [Processing and periodogram conventions](#processing-and-periodogram-conventions)
- [Optional source localization](#optional-source-localization)
- [Command-line reference](#command-line-reference)
- [Outputs and provenance](#outputs-and-provenance)
- [Troubleshooting](#troubleshooting)
- [Reproducibility and testing](#reproducibility-and-testing)
- [Citation, license, and artwork](#citation-license-and-artwork)

## Capabilities and scope

- Search by TIC ID or unambiguous ICRS coordinate counterpart.
- Explicitly select `mission="TESS"`, `author="SPOC"`, and 20-s or 120-s exposure time.
- Retrieve all available sectors or a specified subset.
- Use PDCSAP flux by default, or request SAP explicitly.
- Apply a configurable quality mask, remove invalid measurements, and normalize sectors independently.
- Save light curves, Lomb–Scargle amplitude spectra, diagnostic plots, and a provenance/error manifest.
- Optionally stitch sectors **separately for each cadence**.
- Optionally download matched target-pixel files and call TESS-Localize for selected frequencies.

**This is pipeline light-curve retrieval, not custom-aperture photometry.** The workflow downloads existing SPOC aperture light curves. Target-pixel files are used only for optional localization. It does not generate missing USC/SC observations, silently substitute full-frame-image products, select community-produced light curves, identify pulsation modes, or automatically certify a detection.

## Installation

### Requirements

- Python 3.10 or later.
- Lightkurve 2.5 or later within major version 2.
- NumPy, Matplotlib, Astropy, and Astroquery; installed automatically with the package.
- Internet access for dependency installation and online MAST/TIC/Gaia operations.

### Install from the extracted source

Open a terminal in the directory containing `pyproject.toml`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
lc-tess --help
```

On Windows PowerShell, replace the activation command with:

```powershell
.venv\Scripts\Activate.ps1
```

If the executable cannot be found, use the same Python environment and run:

```bash
python -m lc_tess --help
```

Do not assume a package has already been published on PyPI under this name. These instructions install the supplied source directory. No separate wheel download is needed.

### Optional localization dependency

```bash
python -m pip install ".[localize]"
```

The package is installed separately as `tess-localize` and imported as `TESS_Localize`. If installation conflicts with your environment, follow the [upstream installation guidance](https://github.com/Higgins00/TESS-Localize) in a dedicated environment. No upstream dependency source code is included in this repository.

## Quick start

### 1. Inspect available products

```bash
lc-tess --tic 422526868 --search-only
```

The identifier is a usage example, not a guarantee of particular sectors or cadences. Inspect the printed products and saved search inventories before a large download.

### 2. Retrieve available USC and SC light curves

```bash
lc-tess --tic 422526868 --cadence both --output results
```

The workflow handles 20-s and 120-s products independently. A missing cadence is reported; the tool does not fabricate or resample missing observations.

### 3. Restrict the sector and frequency interval

```bash
lc-tess --tic 422526868 --cadence sc --sectors 42 --fmin 100 --fmax 4000 --output results_sc
```

Frequency arguments are in **microhertz**. Sector 42 is an example: first confirm the requested product exists. For 20-s products use `--cadence usc`.

### 4. Optionally combine sectors

```bash
lc-tess --tic 422526868 --cadence both --stitch --output results_stitched
```

Per-sector products are retained, and an additional combined product is made for each cadence with at least two successfully processed sectors. The pipeline does not mix USC with SC or interpolate gaps.

### Notebook interface

A clean, unexecuted tutorial is provided in [examples/quickstart.ipynb](examples/quickstart.ipynb). Run it in a Jupyter environment containing the installed package. It has no embedded observations, private notebook outputs, or automatic localization of placeholder frequencies.

## Coordinates and target matching

Provide ICRS RA and declination in **decimal degrees**, not sexagesimal strings. Replace the placeholders below with numerical values:

```bash
lc-tess --ra YOUR_RA_DEG --dec YOUR_DEC_DEG --radius 5 --search-only
```

The radius is in arcseconds. The software queries the TIC catalog and proceeds only if one unique TIC identifier falls within the radius. If multiple counterparts are found, it lists them and stops; confirm the correct source and rerun with `--tic`.

A unique coordinate counterpart is not proof that a measured signal originates from it. Inspect field contamination, proper motion, catalog epoch, aperture geometry, and the localization results. Coordinate-resolution failures occur before the target-specific output directory can be created, so they may appear only in terminal output.

## Processing and periodogram conventions

### Quality filtering and normalization

The default Lightkurve quality-bit mask is `default`. Additional sigma clipping and flattening are **off** by default. Invalid times/fluxes and nonpositive or invalid flux errors are excluded; at least ten valid points are required. The surviving data are sorted by time, and duplicate times are rejected rather than silently averaged.

Each sector is normalized to zero-centered relative flux:

```math
\delta F_{\rm ppt}=1000\left(\frac{F}{\operatorname{median}(F)}-1\right).
```

The flux errors are scaled by the same median. One ppt corresponds to relative flux 0.001. The uncertainty in the normalization factor and pipeline-induced correlations are not included in the exported errors.

PDCSAP is already pipeline corrected. SAP is an explicitly requested alternative and is **not** detrended or contamination corrected by this wrapper merely by choosing `--flux sap_flux`.

### Optional clipping and flattening

```bash
lc-tess --tic 422526868 --sigma 5 --flatten-window 1001 --output results_filtered
```

This example illustrates optional processing, not a recommended universal setting. The window is an odd integer count of **cadences**, so its duration differs by a factor of six between USC and SC. Flattening or clipping can attenuate pulsations or distort eclipses/outbursts. Inspect the unfiltered products and validate the effects before adopting these options for science.

The manifest records selected settings and final point counts, but not a full per-point rejection audit or trend model. Keep original FITS products and settings if such an audit is required.

### Lomb–Scargle spectra

The code uses Lightkurve's Lomb–Scargle interface with:

```python
normalization="amplitude"
freq_unit=astropy.units.uHz
ls_method="fast"
```

This produces an **unweighted amplitude spectrum** in the input flux units (ppt). Photometric errors are exported but are not supplied as periodogram weights. The result is not a power spectral density, a formal likelihood surface, a false-alarm probability, or a calibrated significance statistic.

The implementation does not apply `sqrt(4*PSD/N)` to an error-weighted, dimensionless PSD and label it a physical amplitude. For publication-level amplitudes and uncertainties, fit sinusoids using an appropriate error model and inspect aliases/window effects.

Default frequency bounds:

| Cadence | Nominal cadence Nyquist | Default upper bound |
|---|---:|---:|
| SC, 120 s | 4166.67 microhertz | 0.99 times the nominal value |
| USC, 20 s | 25000 microhertz | 0.99 times the nominal value |

The default lower bound is 1/time baseline. Barycentric timing and gaps make these cadence-based Nyquist values reference scales rather than exact limits for every inference. Searching above them requires `--super-nyquist`; this flag does not resolve aliases.

Finite integration suppresses high-frequency amplitudes. **No integration-time correction is applied.** Grid oversampling samples peaks more finely but does not increase independent frequency resolution. The default is 5; the tool does not assume that one oversampling choice uniquely confirms or removes a signal.

No automatic detection threshold, frequency uncertainty, spectral-window calculation, prewhitening, or pulsation-mode identification is performed. A peak is not automatically called a detection.

Long-baseline stitched spectra can require large grids. `--max-bins` guards against oversized calculations. Narrow the frequency range or analyze sectors independently before increasing this limit.

## Optional source localization

Select frequencies that have been independently assessed and are believed to arise from the **same source**. For example:

```bash
lc-tess --tic 422526868 --cadence sc --sectors 42 --frequencies 1000 1500 --pca 3 --output results_localize
```

The two frequencies above are syntax examples, **not measured signals for the example TIC**. Replace them and the sector with the appropriate values. The wrapper does not automatically select significant peaks, group unrelated signals, or optimize the PCA count.

For each successfully processed sector/cadence, it searches for exactly one corresponding SPOC target-pixel file. It checks target/sector metadata and calls the upstream API:

```python
import astropy.units as u
import TESS_Localize as tl

result = tl.Localize(
    targetpixelfile=tpf,
    gaia=True,
    magnitude_limit=18,
    frequencies=selected_frequencies_uhz,
    frequnit=u.uHz,
    principal_components=3,
)
result.info()
```

The wrapper also calls `pca()` and `plot(frequencylist_index=0, method="snr")`, capturing text and saving generated figures. The explicit SNR plot selects the first listed frequency; additional figures follow upstream behavior. Structured localization posterior tables are not invented or exported by this wrapper.

**Localization and PDCSAP extraction are different analysis paths.** Localization uses the original TPF, its quality mask, and upstream processing—not the exported PDCSAP series or its optional clipping/flattening. Frequencies are supplied to each selected sector unchanged, so a signal absent or changed in a particular sector may localize poorly. Do not combine frequencies from different contaminating sources in one source hypothesis.

Gaia/network access and upstream compatibility are required. A missing, ambiguous, or failed TPF/localization step is recorded without discarding successful light-curve analysis. Source rankings, likelihood measures, and p-values should not be treated as interchangeable probabilities of astrophysical truth.

Reference: [Higgins & Bell (2023), AJ, 165, 141](https://doi.org/10.3847/1538-3881/acb20c). See the [upstream repository](https://github.com/Higgins00/TESS-Localize) for interpretation and installation details.

## Command-line reference

| Option | Default | Meaning |
|---|---|---|
| `--tic ID` | Required alternative | TIC identifier; not used with coordinates |
| `--ra DEG --dec DEG` | Required alternative | ICRS coordinates in decimal degrees |
| `--radius ARCSEC` | 5 | TIC coordinate-match radius |
| `--cadence {usc,sc,both}` | both | 20 s, 120 s, or both |
| `--sectors N [N ...]` | all available | Selected sectors |
| `--flux {pdcsap_flux,sap_flux}` | pdcsap_flux | Pipeline flux column |
| `--quality {default,hard,hardest,none}` | default | Lightkurve quality mask |
| `--sigma VALUE` | off | Additional flux sigma clipping |
| `--flatten-window N` | off | Odd smoothing-window size in cadences |
| `--fmin VALUE`, `--fmax VALUE` | sampling-based | Frequency bounds in microhertz |
| `--oversample N` | 5 | Frequency-grid oversampling |
| `--max-bins N` | 2000000 | Grid-size guard |
| `--super-nyquist` | off | Permit upper frequency above nominal Nyquist |
| `--stitch` | off | Also combine sectors separately by cadence |
| `--search-only` | off | Search/save inventories, without LC downloads |
| `--frequencies F [F ...]` | none | Same-source localization frequencies in microhertz |
| `--pca N` | 3 | Localization PCA component count |
| `--magnitude-limit MAG` | 18 | Localization Gaia magnitude limit |
| `--output DIR` | results | Output parent directory |
| `--cache DIR` | .cache/lightkurve | Archive FITS cache |
| `--version`, `--help` | — | Version and command help |

## Outputs and provenance

A typical run writes:

```text
results/TIC_<id>/
├── manifest.json
├── search_20s.ecsv
├── search_120s.ecsv
├── TIC_<id>_s<sector>_20s_lc.csv
├── TIC_<id>_s<sector>_20s_lsp.csv
├── TIC_<id>_s<sector>_20s_diagnostics.png
├── TIC_<id>_s<sector>_120s_lc.csv
├── TIC_<id>_s<sector>_120s_lsp.csv
└── TIC_<id>_s<sector>_120s_diagnostics.png
```

Only available/processed products generate their corresponding files. Empty searches are recorded in the manifest rather than written as empty ECSV tables.

| Product | Columns or contents |
|---|---|
| `*_lc.csv` | `bjd_tdb`, `delta_flux_ppt`, `flux_err_ppt` |
| `*_lsp.csv` | `frequency_uhz`, `frequency_cpd`, `amplitude_ppt` |
| `*_diagnostics.png` | Light curve and amplitude spectrum |
| `search_*s.ecsv` | Archive product inventory |
| `manifest.json` | Input, UTC run times, versions, target match, product rows, processing settings, errors |
| `*_tpf_search.ecsv` | Optional localization TPF inventory |
| `*_localize.txt` | Captured localization text |
| `*_localize_<n>.png` | Saved upstream figures |
| `*_stitched_*s_*` | Optional combined-sector products for one cadence |

CSV time is **full BJD_TDB**, not BTJD. Figure times are BJD_TDB minus 2457000. Frequency conversion is `cycles/day = microhertz × 0.0864`.

Downloaded original FITS files remain in the selected cache; they are not committed to this repository or copied automatically into the result directory. Preserve them or the recorded product identifiers for reproducibility.

Only one product per sector/cadence is attempted after a sector is first encountered. Further duplicates are reported as errors rather than merged. The code does not automatically choose the best reprocessing version; inspect inventory/product rows and verify the desired archive release.

**Use a new output directory for each distinct run.** Matching filenames are overwritten, and stale files from previous runs are not automatically removed.

Exit status:

- `0`: completed without recorded processing errors; a search-only run may still find zero products.
- `1`: fatal failure or no successfully analyzed light curves.
- `2`: partial success with product, localization, or stitching errors.

Always inspect `manifest.json`, not just the existence of a plot. A terminal error before target resolution may not produce a manifest.

## Troubleshooting

| Problem | Check or action |
|---|---|
| `lc-tess` not found | Activate the environment or use `python -m lc_tess` |
| No products | Verify TIC, requested sector, cadence and SPOC availability with `--search-only` |
| Ambiguous coordinate match | Inspect candidates, confirm the source, rerun with `--tic` |
| Invalid flux/errors | Compare original FITS columns and selected flux type; no fake errors are substituted |
| Duplicate time/product error | Review archive product versions and time overlap; no silent averaging is done |
| Grid too large | Narrow the frequency interval or analyze sectors individually |
| Localization import/install failure | Install the extra in a clean environment and check upstream compatibility |
| Localization fails | Check TPF availability, selected frequencies, sector variability, network/Gaia and PCA settings |
| Unexpected signal or amplitude | Inspect SAP/PDCSAP differences, aperture contamination, quality flags, filtering and aliases |
| Missing graphical display | Use a noninteractive backend as shown below |

For a headless Linux server:

```bash
MPLBACKEND=Agg lc-tess --tic 422526868 --cadence both --output results
```

The package saves figures without requiring a GUI. Upstream localization may have its own plotting behavior.

## Reproducibility and testing

Record the command, input, code version/commit, environment, archive inventory, cache location and manifest. For example:

```bash
python --version
lc-tess --version
python -m pip freeze > requirements-used.txt
```

Install development dependencies and run tests:

```bash
python -m pip install -e ".[dev]"
MPLBACKEND=Agg python -m pytest -q
```

The generation environment passed **20 dependency-light tests**; **one integration-test module was skipped** because Lightkurve/Astropy were absent. The skipped test contains an explicitly analytical sine-wave fixture for amplitude and unit validation, not an observation. GitHub Actions is configured to install runtime dependencies and execute it; that workflow has not yet run on your repository.

No live MAST/TIC/Gaia or TESS-Localize run is claimed. Complete [VALIDATION.md](VALIDATION.md), pin the validated environment, and confirm publication permission before a stable release. Passing software tests does not by itself validate a scientific interpretation.

The original research notebooks informed the public workflow; private paths, ground-based reduction cells, lists, notebook outputs and forced process exits were excluded.

## Citation, license, and artwork

Cite the exact release used; [CITATION.cff](CITATION.cff) supplies metadata without inventing a DOI. Follow the citation/acknowledgment requirements of Lightkurve, TESS/SPOC, MAST, Astropy, Astroquery and Gaia when applicable. Cite Higgins & Bell (2023) if TESS-Localize contributes to the analysis.

Original code: copyright (c) 2026 Murat Uzundag, under the [MIT License](LICENSE). Dependencies retain their own licensing terms; see [THIRD_PARTY.md](THIRD_PARTY.md). The repository license does not override any upstream redistribution obligations.

The black-background emblem uses the supplied red–white–blue pulsation-sphere artwork. Its cyan wave and orbit are decorative, not data. The second supplied image was blank. See [assets/README.md](assets/README.md) for provenance and confirm permission to redistribute the source sphere.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contributions and [UPLOAD_TO_GITHUB.md](UPLOAD_TO_GITHUB.md) for initial upload instructions. The archive is a prepared source tree, not an action that creates or publishes a GitHub repository automatically.
