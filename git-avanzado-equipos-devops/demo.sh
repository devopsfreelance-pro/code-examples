#!/bin/bash
# demo.sh
#
# Demuestra en un repo Git temporal el flujo de hooks descripto en el post:
#   1. Un pre-commit que bloquea credenciales hardcodeadas.
#   2. Un commit-msg que exige Conventional Commits.
#   3. Un flujo trunk-based: rama corta de feature -> merge a main.
#
# No modifica nada fuera de /tmp. Se puede correr las veces que haga falta.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_DIR="$(mktemp -d /tmp/git-avanzado-demo.XXXXXX)"

echo "== Repo de demo en: $DEMO_DIR =="
cd "$DEMO_DIR"

git init -q -b main
git config user.email "demo@example.com"
git config user.name "Demo User"

mkdir -p .git/hooks
cp "$SCRIPT_DIR/hooks/pre-commit" .git/hooks/pre-commit
cp "$SCRIPT_DIR/hooks/commit-msg" .git/hooks/commit-msg
chmod +x .git/hooks/pre-commit .git/hooks/commit-msg

echo
echo "== 1) Commit inicial en main =="
echo "# Proyecto demo" > README.md
git add README.md
git commit -q -m "chore: commit inicial"
echo "OK: commit inicial creado"

echo
echo "== 2) Pre-commit hook: intento de commitear una credencial (debe FALLAR) =="
echo 'api_key = "sk-1234567890abcdef"' > config.py
git add config.py
if git commit -m "feat: add config" 2>/tmp/git-avanzado-demo-stderr.txt; then
    echo "ERROR INESPERADO: el commit con credencial no fue bloqueado"
    exit 1
else
    echo "OK: el hook bloqueó el commit con credencial hardcodeada, como se esperaba"
    cat /tmp/git-avanzado-demo-stderr.txt || true
fi
git reset -q HEAD config.py
rm -f config.py

echo
echo "== 3) Commit-msg hook: mensaje que NO sigue Conventional Commits (debe FALLAR) =="
echo "print('hola')" > app.py
git add app.py
if git commit -m "arreglo cosas" 2>/tmp/git-avanzado-demo-stderr.txt; then
    echo "ERROR INESPERADO: el commit con mensaje inválido no fue bloqueado"
    exit 1
else
    echo "OK: el hook bloqueó el mensaje que no sigue Conventional Commits"
    cat /tmp/git-avanzado-demo-stderr.txt || true
fi

echo
echo "== 4) Commit válido siguiendo Trunk-Based Development =="
git checkout -q -b feature/add-app
git commit -q -m "feat(app): add hello world script"
echo "OK: commit válido en rama de feature de corta duración"

git checkout -q main
git merge -q --no-ff feature/add-app -m "chore: merge feature/add-app into main"
git branch -q -d feature/add-app
echo "OK: merge a main y rama de feature eliminada (ciclo cerrado en minutos)"

echo
echo "== Historial final =="
git log --oneline --graph --all

echo
echo "== Demo completa. Repo temporal: $DEMO_DIR (podés borrarlo con: rm -rf $DEMO_DIR) =="
