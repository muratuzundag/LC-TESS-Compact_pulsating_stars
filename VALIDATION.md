# Validation and release checklist

## Completed in generation environment

- Python syntax checked for all source/test files and notebook code cells.
- 20 dependency-light tests passed.
- README internal links, local file references and image dimensions checked.
- Compressed source archive inspected for hidden configuration and unwanted files.

## Not completed here

- Full clean-environment runtime installation: NOT executed.
- Offline Lightkurve integration module: SKIPPED (Lightkurve/Astropy unavailable).
- Live SPOC LC/TPF retrieval and TIC/Gaia queries: NOT executed.
- Real TESS-Localize analysis: NOT executed.
- GitHub Actions execution on the destination repository: NOT executed.
- Publication/redistribution rights for supplied artwork or coauthored notebooks:
  require confirmation by the owner.

## Before advertising a stable scientific release

1. Install cleanly on a supported Python version and run all tests, including the
   analytical amplitude/unit integration test. Record dependency versions.
2. Inventory and download known available SC and USC products. Confirm TICID,
   sector, exposure time, flux origin and BJD_TDB conversion against FITS files.
3. Inspect pipeline quality filtering and unit/error normalization.
4. Check all-sector runs, duplicate/reprocessed products, absent cadences and
   target/coordinate ambiguity. Test cached repeat runs and service failures.
5. Validate periodogram amplitude accuracy, sampling aliases and filtering
   attenuation for the intended science case, including gaps and long baselines.
6. Compare localization for a known variable source with the upstream tutorial,
   reviewing PCA selection, frequency grouping and per-sector signal presence.
7. Review dependencies, licenses, references and artwork permissions, then tag
   and archive the validated release. A DOI must not be claimed until assigned.

These checks do not establish universal statistical coverage or correct physical
interpretation; source contamination and mode identification remain scientific
judgments. This archive is a release candidate, not a claim that these steps
have already been completed.
