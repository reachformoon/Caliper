#!/usr/bin/env bash
cd /d/Caliper || exit 1
git add -A && git -c core.quotepath=false commit -m "docs: verify WSL 4GB limit, add registry mirror and startup notes" | tail -2
git log --oneline | head -2
