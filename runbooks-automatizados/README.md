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
