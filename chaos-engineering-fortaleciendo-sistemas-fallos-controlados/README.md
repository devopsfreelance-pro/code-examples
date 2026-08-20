# Chaos Engineering: mini Chaos Monkey contra un servicio real

Post: [Chaos Engineering: Fortaleciendo Sistemas con Fallos Controlados](https://www.devopsfreelance.pro/blog/posts/chaos-engineering-fortaleciendo-sistemas-fallos-controlados/)

## Que demuestra

El post incluye un ejemplo de codigo *conceptual* con las funciones
`hypothesis_steady_state()`, `inject_failure()` y `verify_recovery()`, pero
llama a funciones que no existen (`measure_availability`,
`terminate_instance`, etc.). Este mini-proyecto convierte exactamente esa
misma estructura en algo que corre de verdad, contra contenedores reales:

1. **`hypothesis_steady_state()`**: confirma que las 3 instancias de un
   `payment-service` de juguete estan saludables (100% de disponibilidad)
   antes de tocar nada.
2. **`inject_failure()`**: elige una instancia al azar entre los
   contenedores etiquetados `chaos.target=payment-service` y la mata con
   `docker kill`, igual que Chaos Monkey terminaba instancias de EC2 en
   Netflix.
3. **`verify_recovery()`**: espera el periodo de recuperacion y vuelve a
   medir la disponibilidad. Docker Compose reinicia automaticamente el
   contenedor caido gracias a `restart: unless-stopped`, simulando el
   auto-healing de un orquestador real sin intervencion humana.

El "payment-service" es un servidor HTTP minimo en Python (solo libreria
estandar) que expone `GET /health`, corriendo como 3 instancias
independientes.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Python 3 en el host (para correr `chaos_experiment.py`, solo usa
  libreria estandar: `urllib`, `subprocess`, `json`)
- Puertos libres en el host: `8081`, `8082`, `8083`

## Estructura

```
chaos-engineering-fortaleciendo-sistemas-fallos-controlados/
├── docker-compose.yml     # 3 instancias del payment-service
├── app/app.py             # servidor HTTP minimo (GET /health)
└── chaos_experiment.py    # experimento de chaos engineering
```

## Pasos para correrlo

1. Levantar las 3 instancias del servicio:

   ```bash
   docker compose up -d
   ```

2. Confirmar que las 3 responden (opcional, sanity check manual):

   ```bash
   curl http://localhost:8081/health
   curl http://localhost:8082/health
   curl http://localhost:8083/health
   ```

3. Ejecutar el experimento de caos:

   ```bash
   python3 chaos_experiment.py
   ```

4. Limpiar el entorno al terminar:

   ```bash
   docker compose down
   ```

## Salida esperada

```
=== 1. Hipotesis de estado estable ===
Disponibilidad medida (baseline): 100.0%
OK: estado estable confirmado (3/3 instancias saludables).

=== 2. Inyeccion de fallo: terminar una instancia al azar ===
Instancia terminada: payment-2

=== 3. Verificacion de recuperacion (esperando 8s) ===
Disponibilidad medida (post-recuperacion): 100.0%

=== Resultado del experimento ===
{
  "victim": "payment-2",
  "availability_recovered": true,
  "availability_pct": 100.0
}

OK: el sistema se recupero solo, sin intervencion humana.
```

Cual instancia se elige como victima es aleatorio (`payment-1`,
`payment-2` o `payment-3`), y el tiempo exacto de recuperacion puede
variar segun la maquina. El patron esperado es siempre el mismo: 100% de
disponibilidad -> caida de una instancia -> recuperacion automatica sin
que nadie reinicie nada a mano.

## Ir mas alla

- Subi `RECOVERY_WAIT_SECONDS` en `chaos_experiment.py` si tu Docker tarda
  mas en reiniciar el contenedor caido.
- Corre el experimento en loop (`while true; do python3
  chaos_experiment.py; sleep 5; done`) para ver como se comporta el
  "blast radius" cuando se mata mas de una instancia seguida.
- Este ejemplo usa `docker kill` + `restart: unless-stopped` porque corre
  100% local sin cuenta ni licencia. Herramientas de nivel productivo
  como **Gremlin** o **Chaos Toolkit**, mencionadas en el post, agregan
  orquestacion de experimentos, metricas de negocio y mecanismos de
  aborto automatico sobre esta misma idea base.
