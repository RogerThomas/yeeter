# Releases

`yeetr` uses CalVer based on the release date. Versions are published in
PEP 440 canonical form as `YYYY.M.D`, so a release on 2026-05-21 is
`2026.5.21`; multiple releases on the same day use `.postN`, for example
`2026.5.21.post1`.

Run `task release` to create the `release/{TAG}` PR, then merge it.
Then create and push the matching release tag. GitHub Actions validates
the tag, creates the GitHub Release, and a separate workflow deploys
docs.

If you need to bypass the PR flow, run `task release-direct`. That bumps
the version on `main`, runs `task deps-lock`, commits, pushes `main`,
creates the matching tag, and pushes the tag.

To bump a release version manually, run `uv version <version>`.

Install from PyPI with:

```bash
uv add yeetr
```
