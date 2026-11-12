#!/usr/bin/env bash
cd /d/Caliper || exit 1
echo "== try start Docker Desktop =="
MSYS_NO_PATHCONV=1 cmd /c start "" "C:\Users\69561\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe" 2>&1
echo "start exit=$?"
echo "== wait 45s =="
sleep 45
echo "== processes =="
tasklist 2>&1 | grep -iE "Docker Desktop|com.docker|vmmem" | head -6
echo "== wsl =="
wsl.exe -l -v 2>&1 | tr -d '\000' | head -6
echo "== engine =="
DOCKER="/c/Users/69561/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe"
timeout 20 "$DOCKER" version --format '{{.Server.Version}}' 2>&1; echo "EXIT=$?"
echo "== DONE =="
