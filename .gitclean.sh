#!/usr/bin/env bash
cd /d/Caliper || exit 1
git rm --cached -q .verify6.sh .verify7.sh 2>/dev/null
rm -f .verify6.sh .verify7.sh .docfix.sh
git add -A
git -c core.quotepath=false commit -m "chore: ignore ad-hoc verify scripts" 2>&1 | tail -2
echo "== tracked scripts =="
git ls-files | grep -E "^\.(verify|d0|tmp)" || echo "(none)"
git status --short | head -5
echo "== DONE =="
