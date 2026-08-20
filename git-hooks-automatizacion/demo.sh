#!/bin/bash
# Demo de git hooks del lado del cliente (pre-commit, commit-msg) y del lado
# del servidor (post-receive) descritos en el post "Git Hooks: Guia Completa
# de Automatizacion DevOps 2026".
#
# Crea, dentro de /tmp, un repo "bare" que simula el servidor remoto y un
# clon local que simula la maquina del desarrollador. No toca este
# repositorio en ningun momento.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

WORKDIR=$(mktemp -d /tmp/git-hooks-demo.XXXXXX)
BARE_REPO="$WORKDIR/proyecto.git"
WORK_REPO="$WORKDIR/desarrollador"
PROD_DIR="$WORKDIR/produccion"

echo "== Workdir de la demo: $WORKDIR =="
echo

# 1) Crear el repo bare que simula el servidor remoto, con el hook post-receive
echo "== 1) Creando repo bare (servidor) con hook post-receive =="
git init --bare "$BARE_REPO" -q
cp "$SCRIPT_DIR/hooks/post-receive" "$BARE_REPO/hooks/post-receive"
chmod +x "$BARE_REPO/hooks/post-receive"
echo "OK: repo bare creado en $BARE_REPO"
echo

# 2) Clonar el repo y configurar los hooks del lado del cliente
echo "== 2) Clonando repo e instalando hooks de cliente =="
git clone -q "$BARE_REPO" "$WORK_REPO"
cd "$WORK_REPO"
git config user.email "demo@devopsfreelance.pro"
git config user.name "Demo DevOps"

cp "$SCRIPT_DIR/hooks/pre-commit" .git/hooks/pre-commit
cp "$SCRIPT_DIR/hooks/commit-msg" .git/hooks/commit-msg
chmod +x .git/hooks/pre-commit .git/hooks/commit-msg
echo "OK: hooks pre-commit y commit-msg instalados en $WORK_REPO/.git/hooks"
echo

# 3) Commit inicial valido, incluye un script de deploy que el post-receive
#    va a ejecutar en produccion.
echo "== 3) Commit inicial en main (debe pasar todas las validaciones) =="
cat > README.md <<'EOF'
# App de demo para git hooks
EOF
cat > deploy.sh <<'EOF'
#!/bin/bash
echo "Ejecutando deploy.sh en produccion..."
echo "Version desplegada: $GIT_COMMIT"
echo "Servicio reiniciado (simulado)"
EOF
chmod +x deploy.sh
git add README.md deploy.sh
git commit -q -m "feat: commit inicial con script de deploy"
git branch -M main
echo "OK: commit inicial creado"
echo

echo "== 4) Push a main: dispara el post-receive y despliega a produccion =="
DEMO_PROD_DIR="$PROD_DIR" git push -q origin main 2>&1 | sed "s/^/  /"
echo
echo "Contenido desplegado en produccion:"
ls -la "$PROD_DIR" | sed "s/^/  /"
echo

echo "== 5) Pre-commit hook: intento de commitear un secreto (debe FALLAR) =="
echo 'const api_key = "sk-live-1234567890abcdef";' > config.js
git add config.js
set +e
commit_output=$(git commit -q -m "feat: agrega config con api key" 2>&1)
commit_status=$?
set -e
echo "$commit_output" | sed "s/^/  /"
if [ "$commit_status" -eq 0 ]; then
    echo "FALLO INESPERADO: el commit con secreto no deberia haber pasado"
    exit 1
else
    echo "OK: el hook bloqueo el commit con secreto hardcodeado, como se esperaba"
fi
git reset -q HEAD config.js
rm -f config.js
echo

echo "== 6) Commit-msg hook: mensaje que no sigue Conventional Commits (debe FALLAR) =="
echo "cambio menor" > notas.txt
git add notas.txt
set +e
commit_output=$(git commit -q -m "arreglo rapido sin formato" 2>&1)
commit_status=$?
set -e
echo "$commit_output" | sed "s/^/  /"
if [ "$commit_status" -eq 0 ]; then
    echo "FALLO INESPERADO: el commit con mensaje invalido no deberia haber pasado"
    exit 1
else
    echo "OK: el hook bloqueo el mensaje de commit invalido, como se esperaba"
fi
git commit -q -m "docs: agrega notas del proyecto"
echo "OK: reintentado con formato Conventional Commits, el commit paso"
echo

echo "== 7) Segundo push: nuevo deploy con la version actualizada =="
DEMO_PROD_DIR="$PROD_DIR" git push -q origin main 2>&1 | sed "s/^/  /"
echo

echo "== Demo completa =="
echo "Repo bare (servidor):  $BARE_REPO"
echo "Repo de trabajo:       $WORK_REPO"
echo "Directorio produccion: $PROD_DIR"
echo
echo "Para borrar todo: rm -rf $WORKDIR"
