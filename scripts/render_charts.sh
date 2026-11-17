#!/bin/sh
# Optional PNG export. Install librsvg separately; SVGs need no renderer to run.
set -eu
command -v rsvg-convert >/dev/null
for chart in results/wealth_*.svg results/reentry/wealth_*.svg; do
  [ -f "$chart" ] || continue
  rsvg-convert "$chart" -o "${chart%.svg}.png"
done
