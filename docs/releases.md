# Releases

`yeetr` uses CalVer based on the release date. Versions are published in
PEP 440 canonical form as `YYYY.M.D`, so a release on 2026-05-21 is
`2026.5.21`; multiple releases on the same day use `.postN`, for example
`2026.5.21.post1`.

Run `task release`. It does no local git work — it just dispatches the
`release` workflow on GitHub. That workflow, on a CI runner, computes the
next CalVer version, bumps `pyproject.toml`, updates the lock file,
commits and pushes `main`, creates the matching GitHub Release, publishes
the package to PyPI, and deploys the documentation.

To release a specific version instead of the auto-computed one, pass it
explicitly:

```bash
task release -- 2026.5.21.post1
```

Publishing to PyPI uses [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC) — there is no API token to manage; PyPI trusts the `release`
workflow directly.

Install from PyPI with:

```bash
uv add yeetr
```
