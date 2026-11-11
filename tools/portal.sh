#!/bin/sh
# Refresh and open the local portal: pull main (picks up the CI audit commits), rebuild, open in the browser.
# Run from a clone of the demo repo with GH_HOST=github.com.
set -e
export GH_HOST=github.com
git fetch -q origin
git checkout -q main
git reset -q --hard origin/main
python3 tools/build_portal.py
open site/index.html 2>/dev/null || xdg-open site/index.html
