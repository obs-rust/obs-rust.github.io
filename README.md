# obs-rust.github.io

The org site for [obs-rust](https://github.com/obs-rust), served at **https://obs-rust.com**.

Static HTML/CSS, no build step. `CNAME` pins the custom domain; `.github/workflows/pages.yml`
publishes the repo root to GitHub Pages from `main`.

Brand assets (mascot badge, logos) come from [obs-rust/brand](https://github.com/obs-rust/brand).
The mascot is inlined in `index.html` so the hero renders without a second request; the source
copy lives at `assets/obs-rust-badge.svg`.
