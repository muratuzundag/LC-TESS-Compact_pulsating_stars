# Contributing

Open an issue before changing a scientific convention, archive selection rule,
flux normalization, or localization behavior. Include a reproducible command,
software versions and a minimal input example you may legally share.

Install the development environment with `python -m pip install -e ".[dev]"`
and run `MPLBACKEND=Agg python -m pytest -q`. Add tests for changed behavior and
state explicitly which archive/Gaia/localization checks were performed live.
Do not commit FITS caches, access tokens, private data or generated notebook outputs.

Changes to signal processing should assess attenuation, aliasing, false-alarm
interpretation and error propagation rather than only visual appearance.
