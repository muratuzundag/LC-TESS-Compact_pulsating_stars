# Upload this complete source repository

Use the final archive from this response, not the older preliminary bundle.
It already includes code, the revised README, logo, examples, tests and metadata.

1. Extract the `.tar.gz` archive on your computer.
2. Open the extracted `LC-TESS-Compact-Pulsating-Stars` directory.
3. On GitHub create a repository named `LC-TESS-Compact-Pulsating-Stars`.
4. Choose Public when ready to share. Leave automatic README, .gitignore and
   license creation OFF/None: the supplied tree already contains those files.
5. Click **uploading an existing file**, or **Add file → Upload files**.
6. Upload the CONTENTS of the extracted directory, not just the compressed file
   and not an additional enclosing directory.
7. Include `.github/` and `.gitignore`. Linux file managers commonly show hidden
   files with Ctrl+H; macOS Finder uses Command+Shift+period.
8. Commit with `Initial LC TESS source upload`.

At repository root, `README.md`, `pyproject.toml`, `src/`, `assets/`, `tests/`
and `examples/` should be directly visible. The banner then appears automatically
through its README-relative image link. If a browser workflow upload is rejected,
use Git or the Actions editor rather than deleting tests from the project.

## Git alternative for a NEW EMPTY remote

Open a terminal inside the extracted directory, replace YOUR_USERNAME and run:

```bash
git init -b main
git add .
git commit -m "Initial LC TESS source upload"
git remote add origin https://github.com/YOUR_USERNAME/LC-TESS-Compact-Pulsating-Stars.git
git push -u origin main
```

Authentication must be configured. For a remote with existing commits, clone it,
copy this source tree into the clone and commit normally; do not force-push just
to upload the bundle.

Do not upload FITS caches, virtual environments, `.egg-info`, `.dist-info`,
`__pycache__`, build folders or original notebooks with private outputs.
Review VALIDATION.md and artwork permissions before a stable public release.
