#!/usr/bin/env bash
cd /d/Caliper || exit 1
echo "== docker =="
timeout 20 docker --version 2>&1
timeout 20 docker compose version 2>&1
echo "-- server --"
timeout 30 docker info --format '{{.ServerVersion}} | {{.OperatingSystem}} | {{.MemTotal}}' 2>&1 | head -3
echo "== images =="
timeout 20 docker images --format '{{.Repository}}:{{.Tag}} | {{.Size}}' 2>&1 | head -20
echo "== hello-world =="
timeout 90 docker run --rm hello-world 2>&1 | head -6
echo "== wsl =="
timeout 15 wsl --status 2>&1 | head -6
echo "== .wslconfig =="
cat /c/Users/69561/.wslconfig 2>&1
echo "== disk =="
df -h /d /c 2>&1 | head -4
echo "== DONE =="
