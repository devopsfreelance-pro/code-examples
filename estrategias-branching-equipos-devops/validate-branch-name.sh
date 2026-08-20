#!/usr/bin/env bash
#
# validate-branch-name.sh
#
# Valida que el nombre de la rama actual (o el que se pase como argumento)
# cumpla con las convenciones de nomenclatura de Git Flow, GitHub Flow o
# GitLab Flow, tal como se describe en el post "Estrategias de Branching en
# Git: Git Flow vs GitHub Flow vs GitLab Flow". Sirve como script de CLI
# standalone o como git hook (pre-push / pre-commit) para evitar ramas con
# nombres inconsistentes.
#
# Uso:
#   ./validate-branch-name.sh                 # valida la rama actual
#   ./validate-branch-name.sh nombre-de-rama   # valida un nombre puntual
#
# Instalar como hook pre-push en un repo existente:
#   cp validate-branch-name.sh .git/hooks/pre-push
#   chmod +x .git/hooks/pre-push

set -euo pipefail

BRANCH_NAME="${1:-$(git branch --show-current 2>/dev/null || true)}"

if [[ -z "${BRANCH_NAME}" ]]; then
  echo "No se pudo determinar el nombre de la rama (¿estas en un repo git con HEAD detached?)." >&2
  exit 1
fi

# Ramas permanentes que no requieren prefijo (Git Flow, GitHub Flow, GitLab Flow)
PERMANENT_BRANCHES=("main" "master" "develop" "staging" "production")

for permanent in "${PERMANENT_BRANCHES[@]}"; do
  if [[ "${BRANCH_NAME}" == "${permanent}" ]]; then
    echo "OK: '${BRANCH_NAME}' es una rama permanente valida."
    exit 0
  fi
done

# Rama de release estilo GitLab Flow, ej: 2-3-stable
if [[ "${BRANCH_NAME}" =~ ^[0-9]+-[0-9]+-stable$ ]]; then
  echo "OK: '${BRANCH_NAME}' sigue la convencion de release estable de GitLab Flow (N-N-stable)."
  exit 0
fi

# Prefijos validos: feature/, release/, hotfix/, bugfix/
VALID_PREFIXES=("feature" "release" "hotfix" "bugfix")
IDENTIFIER_REGEX='^[a-z0-9]+(-[a-z0-9]+)*$'

for prefix in "${VALID_PREFIXES[@]}"; do
  if [[ "${BRANCH_NAME}" == "${prefix}/"* ]]; then
    IDENTIFIER="${BRANCH_NAME#"${prefix}"/}"

    if [[ -z "${IDENTIFIER}" ]]; then
      echo "ERROR: '${BRANCH_NAME}' tiene el prefijo '${prefix}/' pero le falta el identificador." >&2
      exit 1
    fi

    if [[ "${prefix}" == "release" ]]; then
      # release/1.2.0 -> versionado semantico
      if [[ "${IDENTIFIER}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "OK: '${BRANCH_NAME}' sigue la convencion release/<semver>."
        exit 0
      else
        echo "ERROR: '${BRANCH_NAME}' deberia usar versionado semantico, ej: release/1.2.0" >&2
        exit 1
      fi
    fi

    if [[ "${IDENTIFIER}" =~ ${IDENTIFIER_REGEX} ]]; then
      echo "OK: '${BRANCH_NAME}' sigue la convencion ${prefix}/<identificador-en-minusculas-con-guiones>."
      exit 0
    else
      echo "ERROR: '${BRANCH_NAME}' tiene un identificador invalido tras '${prefix}/'." >&2
      echo "       Usa minusculas y guiones, ej: ${prefix}/mi-nueva-caracteristica" >&2
      exit 1
    fi
  fi
done

echo "ERROR: '${BRANCH_NAME}' no cumple ninguna convencion reconocida." >&2
echo "       Prefijos validos: feature/, release/, hotfix/, bugfix/" >&2
echo "       Ramas permanentes validas: main, develop, staging, production" >&2
echo "       Releases GitLab Flow: N-N-stable (ej: 2-3-stable)" >&2
exit 1
