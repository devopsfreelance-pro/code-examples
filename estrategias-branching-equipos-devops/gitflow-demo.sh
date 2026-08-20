#!/usr/bin/env bash
#
# gitflow-demo.sh
#
# Crea un repositorio Git local de prueba y ejecuta el ciclo completo de
# Git Flow (feature branch, release branch y hotfix branch) descrito en el
# post "Estrategias de Branching en Git: Git Flow vs GitHub Flow vs
# GitLab Flow". No usa ningun repositorio remoto: todo corre en un
# directorio temporal para que puedas inspeccionar el historial resultante
# con `git log --all --graph --oneline`.
#
# Uso:
#   ./gitflow-demo.sh [directorio_destino]
#
# Si no se pasa directorio_destino, se crea uno temporal con mktemp.

set -euo pipefail

DEMO_DIR="${1:-$(mktemp -d /tmp/gitflow-demo.XXXXXX)}"

echo "==> Repositorio de demo: ${DEMO_DIR}"
mkdir -p "${DEMO_DIR}"
cd "${DEMO_DIR}"

git init -q -b main
git config user.email "demo@devopsfreelance.pro"
git config user.name "GitFlow Demo"

echo "app version 1.0.0" > VERSION
git add VERSION
git commit -q -m "Commit inicial en main"

echo "==> Creando rama develop desde main"
git checkout -q -b develop

echo "console.log('login pendiente');" > app.js
git add app.js
git commit -q -m "Base de la aplicacion en develop"

echo "==> Feature branch: feature/login-oauth"
git checkout -q -b feature/login-oauth
cat > oauth.js <<'EOF'
function login() {
  return "flujo OAuth implementado";
}
module.exports = { login };
EOF
git add oauth.js
git commit -q -m "Implementar flujo de autorizacion OAuth"
git commit -q --allow-empty -m "Agregar manejo de tokens de refresco"

echo "==> Fusionando feature/login-oauth en develop (--no-ff)"
git checkout -q develop
git merge -q --no-ff feature/login-oauth -m "Merge feature/login-oauth en develop"
git branch -d feature/login-oauth >/dev/null

echo "==> Release branch: release/1.1.0"
git checkout -q -b release/1.1.0
echo "app version 1.1.0" > VERSION
git add VERSION
git commit -q -m "Preparar version 1.1.0"

echo "==> Cerrando release: merge en main y develop + tag"
git checkout -q main
git merge -q --no-ff release/1.1.0 -m "Merge release/1.1.0 en main"
git tag -a v1.1.0 -m "Version 1.1.0"

git checkout -q develop
git merge -q --no-ff release/1.1.0 -m "Merge release/1.1.0 en develop"
git branch -d release/1.1.0 >/dev/null

echo "==> Hotfix urgente: hotfix/vulnerabilidad-sql"
git checkout -q main
git checkout -q -b hotfix/vulnerabilidad-sql
echo "app version 1.1.1" > VERSION
git add VERSION
git commit -q -m "Parchear vulnerabilidad de inyeccion SQL"

echo "==> Cerrando hotfix: merge en main y develop + tag"
git checkout -q main
git merge -q --no-ff hotfix/vulnerabilidad-sql -m "Merge hotfix/vulnerabilidad-sql en main"
git tag -a v1.1.1 -m "Hotfix: correccion de seguridad"

git checkout -q develop
git merge -q --no-ff hotfix/vulnerabilidad-sql -m "Merge hotfix/vulnerabilidad-sql en develop"
git branch -d hotfix/vulnerabilidad-sql >/dev/null

git checkout -q main

echo ""
echo "==> Listo. Historial resultante:"
echo ""
git log --all --graph --decorate --oneline

echo ""
echo "==> Ramas y tags creados:"
git branch --list
git tag --list

echo ""
echo "Repositorio de demo disponible en: ${DEMO_DIR}"
echo "Explora con: cd ${DEMO_DIR} && git log --all --graph --oneline"
