#!/usr/bin/env bash
cd /d/Caliper || exit 1
echo "== version =="
timeout 15 docker --version 2>&1; echo "EXIT=$?"
echo "== compose =="
timeout 15 docker compose version 2>&1; echo "EXIT=$?"
echo "== info =="
timeout 25 docker info > .tmp-dinfo.txt 2>&1; echo "EXIT=$?"; head -6 .tmp-dinfo.txt
echo "== desktop dir =="
ls ~/AppData/Local/Programs/DockerDesktop 2>&1 | head -25
echo "== exe files =="
ls ~/AppData/Local/Programs/DockerDesktop/*.exe 2>&1 | head -6
echo "== service =="
sc query com.docker.service 2>&1 | head -8
echo "== wsl list =="
wsl -l -v 2>&1 | head -8
echo "== docker config =="
ls ~/.docker 2>&1 | head -10
echo "== DONE =="
