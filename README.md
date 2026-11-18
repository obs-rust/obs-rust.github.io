# obs-rust.github.io

The site for [obs-studio-rust](https://github.com/obs-rust/obs-studio), served at **https://obs-rust.com**.

| Path | What |
|---|---|
| `/` | Home: hero, Rust-vs-C crossover gauge, downloads, features ledger, how it's built |
| `/websocket/` | obs-websocket v5 reference (generated from `protocol.json`), with a live in-browser console |
| `/examples/` | Client snippets (Rust, Python, JS, raw), MCP, scripts, plugins, client libraries |
| `/ai/` | Corpus search; `/llms.txt`, `/llms-full.txt`, `/ai/corpus.json`, `/ai/docs/*.md` |

The design is in [DESIGN.md](DESIGN.md), a living document.

## Build

Static output, no framework. `tools/build.py` renders `src/*.html` templates and generates
the API reference and the AI corpus from an obs-studio checkout:

```sh
git clone --depth 1 --filter=blob:none --sparse https://github.com/obs-rust/obs-studio ../obs-rust.github.io-extern/obs-studio
git -C ../obs-rust.github.io-extern/obs-studio sparse-checkout set --no-cone '/*.md' '/docs/' '!/docs/images/' '!/docs/rust-port/native-graph/'
uv run tools/build.py --obs-studio ../obs-rust.github.io-extern/obs-studio   # writes _site/
uv run --no-project python -m http.server 8765 -d _site
```

The tools parse every JSON input into the typed models in `tools/models.py` (pydantic at
the boundaries, frozen dataclasses inside) and are type checked in strict mode:

```sh
uv run tools/check.py _site
uv run --no-project --python 3.12 --with basedpyright==1.40.2 --with 'pydantic>=2.7' \
  --with 'jsonschema>=4.22' --with types-jsonschema basedpyright --level error
uv run tools/site_diff.py OLD_SITE _site   # byte diff, ignoring build timestamps
```

`.github/workflows/pages.yml` does the same on every push to `main`, on dispatch and
daily, then deploys `_site/`. `CNAME` pins the custom domain. Its DNS is at Namecheap:
apex A records point to GitHub Pages, and `www` is a CNAME to `obs-rust.github.io`.

Brand assets come from [obs-rust/brand](https://github.com/obs-rust/brand).
