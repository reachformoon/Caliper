#!/usr/bin/env bash
cd /d/Caliper || exit 1
DOCKER="/c/Users/69561/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe"
echo "== file =="
ls -la "$DOCKER" 2>&1
echo "== direct version =="
"$DOCKER" --version; echo "EXIT=$?"
echo "== direct compose =="
"$DOCKER" compose version; echo "EXIT=$?"
echo "== processes =="
tasklist 2>&1 | grep -iE "docker|vmmem" | head -8
echo "== wsl distros =="
wsl -l -v 2>&1 | iconv -f UTF-16LE -t UTF-8 2>/dev/null | head -8
echo "== ProgramData =="
ls "/c/ProgramData/DockerDesktop" 2>&1 | head -5
echo "== user docker dir =="
ls ~/.docker 2>&1 | head -8
echo "== DONE =="
