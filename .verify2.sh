#!/usr/bin/env bash
cd /d/Caliper || exit 1
echo "== which =="
command -v docker || echo "bash: docker not in PATH"
where.exe docker 2>&1 | head -5
echo "== PATH docker entries =="
echo "$PATH" | tr ':' '\n' | grep -i docker || echo "(none)"
echo "== program files =="
ls "/c/Program Files/Docker/Docker/resources/bin" 2>&1 | head -10
ls "/c/Program Files/Docker/Docker" 2>&1 | head -10
echo "== processes =="
tasklist 2>&1 | grep -i "docker" | head -8
echo "== cmd docker =="
cmd //c "docker --version" 2>&1 | head -3
echo "== cmd compose =="
cmd //c "docker compose version" 2>&1 | head -3
echo "== DONE =="
