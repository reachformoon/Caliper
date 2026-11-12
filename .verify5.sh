#!/usr/bin/env bash
cd /d/Caliper || exit 1
echo "== PATH =="
echo "$PATH" | tr ':' '\n' | head -12
echo "== type -a docker =="
type -a docker 2>&1 | head -5
echo "== cmd /c docker =="
MSYS_NO_PATHCONV=1 cmd /c "docker --version" 2>&1 | head -3
echo "== cmd /c compose =="
MSYS_NO_PATHCONV=1 cmd /c "docker compose version" 2>&1 | head -3
echo "== wsl list raw =="
wsl.exe -l -v 2>&1 | tr -d '\000' | head -8
echo "== wsl status =="
wsl.exe --status 2>&1 | tr -d '\000' | head -6
echo "== docker context =="
cat ~/.docker/config.json 2>&1 | head -20
echo "== DONE =="
