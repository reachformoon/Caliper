#!/usr/bin/env bash
cd /d/Caliper || exit 1
DOCKER="/c/Users/69561/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe"
echo "== images before =="
"$DOCKER" images --format '{{.Repository}}:{{.Tag}} | {{.Size}}' 2>&1 | head -15
echo "== hello-world =="
timeout 180 "$DOCKER" run --rm hello-world 2>&1 | grep -E "Hello|error|Error" | head -3
echo "== pull postgres:16 =="
timeout 900 "$DOCKER" pull postgres:16 2>&1 | tail -3
echo "== pull pgvector =="
timeout 900 "$DOCKER" pull pgvector/pgvector:pg16 2>&1 | tail -3
echo "== images after =="
"$DOCKER" images --format '{{.Repository}}:{{.Tag}} | {{.Size}}' 2>&1 | head -15
echo "== DONE =="
