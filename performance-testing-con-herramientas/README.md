# Performance testing con k6: ejemplo ejecutable

Post: [JMeter: Guía completa de performance testing en 2025](https://www.devopsfreelance.pro/blog/posts/performance-testing-con-herramientas/)

## Qué demuestra este ejemplo

El post compara JMeter y k6 para performance testing. Este ejemplo implementa
en k6 el mismo patrón que se muestra en el post (thread groups / stages con
ramp-up, carga sostenida y ramp-down, más thresholds de latencia y tasa de
error) y lo corre contra una API demo local con dos endpoints:

- `GET /products`: respuesta rápida (~10-30ms).
- `GET /checkout`: respuesta más lenta (~150-400ms), para ver cómo el reporte
  de k6 distingue la latencia entre endpoints.

Se eligió k6 en vez de JMeter para el ejemplo porque el script es un archivo
de pocas líneas versionable en Git ("testing as code"), tal como explica el
post, mientras que un plan de prueba JMeter equivalente requiere un XML mucho
más verboso o la GUI.

## Requisitos

- Docker y Docker Compose (`docker compose version`).
- Ningún otro requisito: la API demo y k6 corren en contenedores, no hace
  falta instalar Python, Flask ni k6 en la máquina.

## Pasos para correrlo

1. Pararse en este directorio:

   ```bash
   cd performance-testing-con-herramientas
   ```

2. Levantar la API demo y correr el load test con k6 en un solo comando:

   ```bash
   docker compose up --build --abort-on-container-exit
   ```

3. Al terminar, limpiar los contenedores:

   ```bash
   docker compose down
   ```

### Correr el test manualmente contra la API ya levantada (opcional)

```bash
docker compose up --build -d demo-api
docker run --rm -i --network performance-testing-con-herramientas_default \
  -v "$(pwd)/k6:/scripts" \
  -e BASE_URL=http://demo-api:5000 \
  grafana/k6:latest run /scripts/load-test.js
docker compose down
```

## Salida esperada

El contenedor `k6` imprime un resumen al final de la corrida (dura ~40
segundos: 10s de ramp-up, 20s de carga sostenida a 20 VUs, 10s de
ramp-down), similar a:

```
     checks.........................: 100.00% ✓ 800      ✗ 0
     http_req_duration..............: avg=95.3ms  p(95)=380ms
       { expected_response:true }...: avg=95.3ms  p(95)=380ms
     http_req_failed................: 0.00%   ✓ 0        ✗ 400
     iterations......................: 400

   ✓ http_req_duration..............: p(95)<500
   ✓ http_req_failed................: rate<0.01
```

Si `p(95)` de `http_req_duration` supera 500ms o `http_req_failed` supera el
1%, k6 marca los thresholds como fallidos y el contenedor termina con código
de salida distinto de 0, tal como se automatizaría en un pipeline CI/CD.

## Estructura

```
performance-testing-con-herramientas/
├── api/                  # API demo (Flask) usada como sistema bajo prueba
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── k6/
│   └── load-test.js      # script de load testing (stages + thresholds)
├── docker-compose.yml    # orquesta demo-api + k6
└── README.md
```
