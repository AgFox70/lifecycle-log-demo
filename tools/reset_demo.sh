#!/bin/sh
# Put the demo back to its starting point: main = demo-baseline, open PRs closed, test branches removed.
# Run from a clone of the demo repo with GH_HOST=github.com and the AgFox70 login. Force-pushes main.
set -e
export GH_HOST=github.com
R=AgFox70/lifecycle-log-demo
git fetch -q origin --tags
git checkout -q main
git reset -q --hard demo-baseline
git push -q --force origin main
for n in $(gh pr list -R $R --state open --json number -q '.[].number'); do gh pr close $n -R $R >/dev/null; done
for b in $(git ls-remote --heads origin 'tmp-*' | sed 's#.*refs/heads/##'); do git push -q origin --delete "$b"; done
echo "Reset: main at $(git rev-parse --short HEAD). Open PRs closed. Open new PRs from the scn-* branches."
