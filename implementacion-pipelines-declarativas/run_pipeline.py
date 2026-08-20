#!/usr/bin/env python3
"""Motor minimo de pipelines declarativas.

Lee un archivo YAML (pipeline.yml) que declara `stages` y `jobs`, y ejecuta
cada job en el orden definido por `stages`, sustituyendo variables y
respetando la clave `when: manual` (se salta salvo que se pase --deploy).

Ilustra el concepto central del post: separar la DECLARACION del proceso
(el YAML, que describe QUE se quiere lograr) de su EJECUCION (este motor,
que decide COMO ejecutarlo), tal como hacen Jenkins (Jenkinsfile) o
GitLab CI (.gitlab-ci.yml).
"""
import argparse
import subprocess
import sys
from pathlib import Path

import yaml


def substitute_vars(text, variables):
    for key, value in variables.items():
        text = text.replace(f"${{{key}}}", str(value))
    return text


def run_job(name, job, variables):
    stage = job.get("stage", name)
    print(f"\n=== stage: {stage} / job: {name} ===")
    for cmd in job.get("script", []):
        cmd = substitute_vars(cmd, variables)
        print(f"$ {cmd}")
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"[FAIL] '{cmd}' salio con codigo {result.returncode}")
            sys.exit(result.returncode)
    print(f"[OK] job '{name}' completado")


def main():
    parser = argparse.ArgumentParser(description="Motor de pipelines declarativas")
    parser.add_argument("pipeline_file", nargs="?", default="pipeline.yml")
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Ejecuta tambien los jobs marcados 'when: manual'",
    )
    args = parser.parse_args()

    path = Path(args.pipeline_file)
    if not path.exists():
        print(f"No se encontro {path}")
        sys.exit(1)

    definition = yaml.safe_load(path.read_text())
    stages = definition.get("stages", [])
    variables = definition.get("variables", {})

    jobs = {
        name: job
        for name, job in definition.items()
        if isinstance(job, dict) and "stage" in job
    }

    print(f"Pipeline declarada con {len(stages)} stages: {', '.join(stages)}")

    for stage in stages:
        stage_jobs = [(n, j) for n, j in jobs.items() if j.get("stage") == stage]
        for name, job in stage_jobs:
            if job.get("when") == "manual" and not args.deploy:
                print(
                    f"\n=== stage: {stage} / job: {name} === "
                    "[SKIPPED] (when: manual, usar --deploy)"
                )
                continue
            run_job(name, job, variables)

    print("\nPipeline completada con exito.")


if __name__ == "__main__":
    main()
