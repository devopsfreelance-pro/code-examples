# Automated Runbooks: minimal engine with pre-checks, steps, and idempotency

Related post: [What Is a Runbook? Practical Guide + Free Templates](https://www.devopsfreelance.pro/blog/en/posts/what-is-a-runbook/)

## What this example demonstrates

The post describes the architecture of an automated runbook (triggers,
execution engine, automation logic, integrations, logging, and
notifications) and its recommended structure (metadata, parameters,
pre-checks, steps, error handling, post-checks). This example
implements that structure in a minimal but real Python engine:

1. `runbooks/cleanup-old-logs.yaml` defines a declarative runbook (metadata,
   params, pre_validations, steps, post_validations, notifications), with the
   same shape as the API latency diagnosis YAML runbook from the post.
2. `runbook_engine.py` is the "execution engine": it loads the YAML, runs
   the pre-checks (aborts if they fail), executes the steps in order with
   explicit error handling, runs the post-checks, and notifies the
   result.
3. The example runbook deletes log files older than N days in a
   test directory, without touching anything on your real system.
4. It supports `--dry-run` (simulation mode, mentioned in the post as a
   security best practice) and **idempotency**: running it twice in a row
   doesn't fail or over-delete the second time.
5. Every execution gets logged to `runbook.log.jsonl` as structured
   logging (JSON Lines), just as recommended in the
   "Monitoring and Maintenance" section of the post.

## Requirements

- Python 3.8+
- `pyyaml` (`pip install pyyaml`)
- No cloud accounts, Docker, or external services: everything runs on
  local files in this directory.

## How to run it

1. Install the only dependency:

```bash
cd runbooks-automatizados
pip install pyyaml
```

2. Generate test data (creates `demo_workspace/logs/` with 3 "old"
   files with mtime forced to 40 days ago and 2 "new" files):

```bash
python3 setup_demo_data.py
```

3. Run the runbook in simulation mode (deletes nothing, just shows what
   it would do):

```bash
python3 runbook_engine.py runbooks/cleanup-old-logs.yaml --dry-run
ls demo_workspace/logs   # all 5 files are still there
```

4. Run the runbook for real:

```bash
python3 runbook_engine.py runbooks/cleanup-old-logs.yaml
ls demo_workspace/logs   # only the 2 "new" files remain
```

5. Run it again (demonstrates idempotency: there are no old files left to
   delete, the runbook finishes OK without doing anything):

```bash
python3 runbook_engine.py runbooks/cleanup-old-logs.yaml
```

6. View the structured log of every execution:

```bash
cat runbook.log.jsonl
```

7. (Optional) Trigger a failed pre-check to see the error handling:
   edit `runbooks/cleanup-old-logs.yaml` and change `target_dir`
   to a directory that doesn't exist, then run the runbook again. The
   engine should abort with `exit code 1` without touching any file.

## Expected output

With `--dry-run`, the console shows something like:

```
[INFO] start: Iniciando runbook 'cleanup-old-logs' (dry_run=True)
[OK] check_directory_exists: Directorio .../demo_workspace/logs verificado
[OK] contar_archivos_viejos: Cuenta cuantos archivos superan max_age_days antes de tocar nada.
[OK] eliminar_archivos_viejos: Elimina los archivos identificados. Idempotente...
[OK] verificar_limpieza: Confirma que no queden archivos viejos en el directorio.
[NOTIFY:console] Limpieza de logs completada
[OK] end: Runbook finalizado con exito
```

In the real run, `ls demo_workspace/logs` goes from 5 files to 2
(`app-hoy.log`, `worker-hoy.log`). If run a third time, the
`eliminar_archivos_viejos` step finds no old files and the runbook finishes
with `exit code 0` and no changes, confirming idempotency.

`runbook.log.jsonl` accumulates one JSON line per event (`pre_validation`,
`step`, `post_validation`), with `status`, `message`, `result`, and `timestamp`,
ready to parse with `jq` or ship to a centralized logging system.

## Cleanup

To leave the directory as it was when you cloned the repo:

```bash
rm -rf demo_workspace runbook.log.jsonl __pycache__
```

---

## 🇪🇸 Versión en español

# Runbooks Automatizados: motor minimo con pre-validaciones, pasos e idempotencia

Post relacionado: [Que es un Runbook: Guia Practica + Plantillas Gratis](https://www.devopsfreelance.pro/blog/posts/runbooks-automatizados/)

## Que demuestra este ejemplo

El post describe la arquitectura de un runbook automatizado (disparadores,
motor de ejecucion, logica de automatizacion, integraciones, logging y
notificacion) y su estructura recomendada (metadatos, parametros,
pre-validaciones, pasos, manejo de errores, post-validaciones). Este ejemplo
implementa esa estructura en un motor Python minimo pero real:

1. `runbooks/cleanup-old-logs.yaml` define un runbook declarativo (metadata,
   params, pre_validations, steps, post_validations, notifications), con la
   misma forma que el runbook YAML de diagnostico de latencia del post.
2. `runbook_engine.py` es el "motor de ejecucion": carga el YAML, corre las
   pre-validaciones (aborta si fallan), ejecuta los pasos en orden con
   manejo de errores explicito, corre las post-validaciones y notifica el
   resultado.
3. El runbook de ejemplo elimina archivos de log con mas de N dias en un
   directorio de prueba, sin tocar nada de tu sistema real.
4. Soporta `--dry-run` (modo simulacion, mencionado en el post como buena
   practica de seguridad) e **idempotencia**: correrlo dos veces seguidas no
   falla ni borra de mas la segunda vez.
5. Cada ejecucion queda registrada en `runbook.log.jsonl` como logging
   estructurado (JSON Lines), igual que recomienda la seccion de
   "Monitoreo y Mantenimiento" del post.

## Requisitos

- Python 3.8+
- `pyyaml` (`pip install pyyaml`)
- Nada de cuentas cloud, Docker ni servicios externos: todo corre sobre
  archivos locales en este directorio.

## Como correrlo

1. Instalar la unica dependencia:

```bash
cd runbooks-automatizados
pip install pyyaml
```

2. Generar datos de prueba (crea `demo_workspace/logs/` con 3 archivos
   "viejos" con mtime forzado a 40 dias atras y 2 archivos "nuevos"):

```bash
python3 setup_demo_data.py
```

3. Correr el runbook en modo simulacion (no borra nada, solo muestra qué
   haria):

```bash
python3 runbook_engine.py runbooks/cleanup-old-logs.yaml --dry-run
ls demo_workspace/logs   # los 5 archivos siguen ahi
```

4. Correr el runbook de verdad:

```bash
python3 runbook_engine.py runbooks/cleanup-old-logs.yaml
ls demo_workspace/logs   # solo quedan los 2 archivos "nuevos"
```

5. Volver a correrlo (demuestra idempotencia: no hay archivos viejos que
   borrar, el runbook termina OK sin hacer nada):

```bash
python3 runbook_engine.py runbooks/cleanup-old-logs.yaml
```

6. Ver el log estructurado de todas las ejecuciones:

```bash
cat runbook.log.jsonl
```

7. (Opcional) Provocar una pre-validacion fallida para ver el manejo de
   errores: editar `runbooks/cleanup-old-logs.yaml` y cambiar `target_dir`
   por un directorio que no exista, luego correr el runbook de nuevo. El
   motor debe abortar con `exit code 1` sin tocar ningun archivo.

## Salida esperada

Con `--dry-run`, la consola muestra algo como:

```
[INFO] start: Iniciando runbook 'cleanup-old-logs' (dry_run=True)
[OK] check_directory_exists: Directorio .../demo_workspace/logs verificado
[OK] contar_archivos_viejos: Cuenta cuantos archivos superan max_age_days antes de tocar nada.
[OK] eliminar_archivos_viejos: Elimina los archivos identificados. Idempotente...
[OK] verificar_limpieza: Confirma que no queden archivos viejos en el directorio.
[NOTIFY:console] Limpieza de logs completada
[OK] end: Runbook finalizado con exito
```

En la ejecucion real, `ls demo_workspace/logs` pasa de 5 archivos a 2
(`app-hoy.log`, `worker-hoy.log`). Si se corre una tercera vez, el paso
`eliminar_archivos_viejos` no encuentra archivos viejos y el runbook termina
en `exit code 0` sin cambios, confirmando la idempotencia.

`runbook.log.jsonl` acumula una linea JSON por evento (`pre_validation`,
`step`, `post_validation`), con `status`, `message`, `result` y `timestamp`,
lista para parsear con `jq` o enviar a un sistema de logs centralizado.

## Limpieza

Para dejar el directorio como al clonar el repo:

```bash
rm -rf demo_workspace runbook.log.jsonl __pycache__
```
