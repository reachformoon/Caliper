#!/usr/bin/env bash
cd /d/Caliper || exit 1
rm -f .finalcheck.sh .pull.sh .restart.sh .wait.sh .mirror-test.sh
git add -A
git -c core.quotepath=false commit -m "chore: ignore ad-hoc docker probe scripts" 2>&1 | tail -2
echo "== status =="
git status --short | head -5
echo "== last =="
git log --oneline | head -3
echo "== .env (masked) =="
sed 's/\(OPENAI_API_KEY=\).*/\1***/' .env 2>/dev/null | head -6
echo "== DONE =="
