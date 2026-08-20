# Optimizar servidor: tuning de red con sysctl (baseline vs tuned)

Ejemplo de código para el post [Optimizar servidor: Técnicas probadas de rendimiento 2025](https://www.devopsfreelance.pro/blog/posts/optimizacion-rendimiento-servidores/).

## Qué demuestra

El post explica la metodología de optimización de servidores: medir una línea
base, identificar el cuello de botella y aplicar cambios incrementales
medibles, usando como ejemplo el tuning de parámetros de red del kernel Linux
(`net.core.somaxconn`, que controla el tamaño de la cola de conexiones
pendientes, y parámetros TCP relacionados).

Este ejemplo levanta **dos contenedores Nginx idénticos**: uno con los
parámetros de red por defecto de Docker/Linux (`nginx-baseline`) y otro con
`net.core.somaxconn=4096` y `net.ipv4.tcp_fin_timeout=15` aplicados vía
`sysctls` de Docker Compose (`nginx-tuned`). Un script de carga
(`load_test.py`) golpea ambos con la misma cantidad de requests concurrentes
y reporta requests/segundo y latencia, permitiendo comparar el efecto real
del tuning, en línea con la metodología "medir antes y después" del post.

## Requisitos

- Docker y Docker Compose (plugin `docker compose`)
- Python 3 (sin dependencias externas, solo librería estándar)

## Pasos para ejecutarlo

```bash
cd optimizacion-rendimiento-servidores

# 1. Levantar los dos servidores (baseline en :8081, tuned en :8082)
docker compose up -d

# 2. Confirmar que el sysctl se aplico dentro del contenedor tuned
docker exec nginx-tuned sysctl net.core.somaxconn net.ipv4.tcp_fin_timeout

# 3. Benchmark del servidor baseline (parametros por defecto)
python3 load_test.py --port 8081 --requests 2000 --concurrency 100

# 4. Benchmark del servidor tuned (somaxconn=4096, tcp_fin_timeout=15)
python3 load_test.py --port 8082 --requests 2000 --concurrency 100

# 5. Apagar los contenedores
docker compose down
```

Para una comparación más marcada, subí la concurrencia (por ejemplo
`--concurrency 300`), que es donde una cola de conexiones pendientes más
chica (`somaxconn` bajo) empieza a descartar o demorar conexiones entrantes.

## Salida esperada

Cada corrida de `load_test.py` imprime algo como:

```
URL objetivo:        http://localhost:8081/
Requests totales:    2000
Concurrencia:        100
Errores:             0
Tiempo total:        1.85 s
Requests/segundo:    1081.3
Latencia promedio:   91.42 ms
Latencia p95:        142.07 ms
```

El servidor `tuned` (puerto 8082) debería mostrar más requests/segundo y
menor latencia p95 que el `baseline` (puerto 8081) a medida que aumenta la
concurrencia, ya que puede aceptar más conexiones pendientes en la cola de
`accept()` en lugar de descartarlas o hacerlas esperar. En equipos con pocos
núcleos o baja concurrencia la diferencia puede ser mínima: ese es
justamente el punto del post, medir antes de asumir que un ajuste va a
generar impacto.

## Notas

- `net.core.somaxconn` y `net.ipv4.tcp_fin_timeout` son sysctls namespaced
  por red, por eso pueden ajustarse por contenedor con la clave `sysctls:`
  de Docker Compose sin necesitar `--privileged` ni tocar el host.
- No hay secretos ni cuentas externas involucradas en este ejemplo.
