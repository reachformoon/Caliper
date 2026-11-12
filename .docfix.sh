#!/usr/bin/env bash
cd /d/Caliper || exit 1
export PYTHONIOENCODING=utf-8
PY=.venv/Scripts/python.exe
echo "== pytest =="; "$PY" -m pytest -q 2>&1 | tail -3
echo "== doctor =="; "$PY" -m caliper doctor 2>&1 | tail -14
git add -A
git -c core.quotepath=false commit -m "feat(cli): doctor detects Docker via install path and checks .env key/model" 2>&1 | tail -2
rm -f .verify-tmp.sh .verify2.sh .verify3.sh .verify4.sh .verify5.sh .verify6.sh .verify7.sh .tmp-dinfo.txt
git status --short | head -5
echo "== DONE =="
