# Dashboards Efectivos con Grafana

Ejemplo ejecutable del post [Dashboards Efectivos con Grafana: Guía Práctica](https://www.devopsfreelance.pro/blog/posts/dashboards-efectivos-con-grafana/).

## Que demuestra

Un stack local con Docker Compose que arma un dashboard de Grafana con los componentes clave que describe el post (paneles, filas, variables y anotaciones), sin depender de ningun servicio pago:

- **node-exporter**: expone metricas reales del host (CPU, memoria, info del sistema) en formato Prometheus.
- **Prometheus**: scrapea `node-exporter` cada 5 segundos.
- **Grafana**: viene provisionado automaticamente con el datasource de Prometheus y el dashboard `node-overview.json`, que incluye:
  - Dos **filas** (`Estado general` / `Uso de recursos`) que agrupan paneles relacionados.
  - Una **variable de plantilla** `$instance` (poblada con `label_values(up{job="node-exporter"}, instance)`) para filtrar los paneles por instancia, tal como explica la seccion "Componentes Clave" del post.
  - Distintos **tipos de panel**: `stat` (instancias UP), `table` (info del host via `node_uname_info`) y `timeseries` (uso de CPU y memoria en %).
  - El sistema de **anotaciones** nativo de Grafana activado (podes marcar un evento manualmente sobre cualquier grafico con Ctrl+Click, como se haria para marcar un despliegue o un incidente).

Es el mismo flujo que describe el articulo: fuente de datos -> consulta y procesamiento -> renderizacion de paneles -> actualizacion automatica (refresh de 5s configurado en el dashboard).

## Requisitos

- Docker y Docker Compose (`docker compose version`)

No requiere cuentas ni servicios pagos: todo corre local en contenedores, usando metricas reales del host donde corras Docker.

## Pasos para correrlo

1. Levantar el stack:

```bash
cd dashboards-efectivos-con-grafana
docker compose up -d
```

2. Verificar que Prometheus tiene el target de `node-exporter` en estado `UP`:

```
http://localhost:9090/targets
```

3. Abrir Grafana (usuario `admin`, password `admin`; pide cambiarla en el primer login, se puede omitir con "Skip"):

```
http://localhost:3000
```

4. Ir a **Dashboards** y abrir **"Node Overview - Dashboard Efectivo Demo"**. Ya esta provisionado, no hace falta importarlo a mano.

5. Probar la variable de plantilla: en la parte superior del dashboard vas a ver el selector **instance**. Cambialo entre "All" y la instancia especifica (`node-exporter:9100`) y observa como se filtran los paneles de tabla, CPU y memoria.

6. Probar una anotacion manual (equivalente a marcar un despliegue o incidente): en cualquiera de los graficos de "Uso de CPU" o "Uso de memoria", hace `Ctrl+Click` (o `Cmd+Click` en Mac) sobre un punto del grafico, cargale una descripcion como "deploy v1.2" y confirma. Vas a ver una linea vertical marcando ese momento en el grafico.

7. Para apagar todo:

```bash
docker compose down
```

## Salida esperada

- En `http://localhost:9090/targets`: el job `node-exporter` en estado `UP`.
- En el dashboard de Grafana, apenas cargue (podes esperar 10-15 segundos para que haya un par de scrapes):
  - El panel **"Instancias UP"** en verde mostrando `1`.
  - El panel **"Informacion del host"** con una fila mostrando `sysname`, `release`, `nodename`, etc. del contenedor `node-exporter`.
  - Los paneles **"Uso de CPU (%)"** y **"Uso de memoria (%)"** graficando una linea que se actualiza cada 5 segundos, con valores entre 0 y 100.
- Cambiar el selector `$instance` filtra los tres paneles de metricas por esa instancia (en este demo hay una sola, pero el mecanismo es el mismo que usarias con varios nodos o servicios en un cluster real).
- La anotacion manual queda visible como una linea vertical roja en los graficos de timeseries, con el texto que le pusiste al pasar el mouse por encima.

## Notas

- Este ejemplo usa `node-exporter` (metricas del host) en vez de metricas de Kubernetes para que corra en minutos solo con Docker, sin necesitar un cluster. El concepto de dashboard (paneles + filas + variables + anotaciones) es el mismo que se usaria con `kube-state-metrics` para el panel de "Estado de Pods por Namespace" que menciona el post.
- Las credenciales de Grafana (`admin`/`admin`) son solo para este entorno local descartable. No usar en un entorno real sin cambiarlas.
- Para reglas de alerta reales sobre estas metricas, ver el ejemplo del post [Monitoreo con Prometheus y Grafana](https://www.devopsfreelance.pro/blog/posts/monitoreo-con-prometheus-grafana/), que cubre esa parte en detalle.
