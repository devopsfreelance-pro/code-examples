FROM jenkins/jenkins:lts-jdk17

USER root

# Node.js para el stage de test de la app de ejemplo (no requiere plugins extra)
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# Plugins minimos para un pipeline declarativo + vista de stages
RUN jenkins-plugin-cli --plugins \
    workflow-aggregator \
    git \
    pipeline-stage-view \
    timestamper

USER jenkins
