# Go para herramientas DevOps: CLI de ejemplo con Cobra

Código de ejemplo para el post [Golang DevOps: Guía completa para herramientas modernas](https://www.devopsfreelance.pro/blog/posts/go-herramientas-devops/).

## Qué demuestra este ejemplo

Un CLI mínimo en Go (`devtool`) que ilustra los tres conceptos centrales del post:

1. **CLI con Cobra**: subcomandos (`deploy`, `status`) con flags, siguiendo el mismo patrón `rootCmd` / `AddCommand` que muestra el artículo.
2. **Manejo de errores explícito**: `deployApplication` envuelve cada error con `fmt.Errorf("...: %w", err)`, el patrón que el post describe como "verboso pero confiable".
3. **Concurrencia con goroutines**: `status` consulta varios hosts en paralelo con goroutines + `sync.WaitGroup` + channel, mostrando que el tiempo total es el de la consulta más lenta, no la suma de todas (a diferencia de un chequeo secuencial).

También incluye tests table-driven con `t.Run`, el mismo patrón de testing que aparece en el post.

## Requisitos

- Go 1.25 o superior (`go version`)
- Sin dependencias externas de infraestructura: no necesita Docker, Kubernetes ni cuentas cloud. Las dependencias de Go (`cobra`, `yaml.v3`) se descargan automáticamente con `go build`/`go test`.

## Pasos para ejecutarlo

Desde este directorio:

```bash
# 1. Descargar dependencias y compilar el binario
go build -o devtool .

# 2. Desplegar usando el manifest de ejemplo (entorno staging por defecto)
./devtool deploy --manifest manifest.yaml

# 3. Desplegar a production explícitamente
./devtool deploy --env production --manifest manifest.yaml

# 4. Consultar el estado de varios hosts en paralelo (goroutines)
./devtool status --hosts web-01,web-02,web-03

# 5. Correr los tests (incluye tests table-driven de validación y despliegue)
go test ./... -v

# 6. (Opcional) Compilación cruzada, tal como se muestra en el post
GOOS=linux GOARCH=amd64 go build -o devtool-linux-amd64
GOOS=darwin GOARCH=amd64 go build -o devtool-darwin-amd64
GOOS=windows GOARCH=amd64 go build -o devtool-windows-amd64.exe
```

## Salida esperada

### `./devtool deploy --env production --manifest manifest.yaml`

```
Desplegando checkout-service en entorno: production
  imagen:   registry.example.com/checkout-service:1.4.0
  replicas: 3
  puertos:  [8080 9100]
Despliegue simulado completado con exito.
```

### `./devtool status --hosts web-01,web-02,web-03`

```
Consultando 3 hosts en paralelo...

  web-03     OK   latencia=75ms
  web-01     OK   latencia=89ms
  web-02     OK   latencia=204ms

Tiempo total: 204.945476ms (secuencial hubiera tardado la suma de cada latencia)
```

Las latencias son aleatorias (simulan un healthcheck de red), pero el tiempo total siempre será cercano a la latencia más alta individual, no a la suma de las tres. Eso es lo que demuestra el uso de goroutines frente a un chequeo secuencial.

### Caso de error (entorno inválido)

```bash
./devtool deploy --env invalid
```

```
Error: entorno invalido: "invalid" (valores validos: staging, production)
```

### `go test ./... -v`

Todos los subtests de `TestDeployApplication` y `TestValidateManifest` deben pasar (`PASS`), incluyendo los casos de manifest inválido, entorno inválido y archivo inexistente.

## Archivos

- `main.go` — comandos raíz `deploy` y `status` definidos con Cobra.
- `deploy.go` — carga y validación del manifest YAML, patrón de errores envueltos con `%w`.
- `status.go` — chequeo concurrente de hosts con goroutines y channels.
- `manifest.yaml` — manifest de ejemplo válido, usado por el comando `deploy`.
- `deploy_test.go` — tests table-driven para `deployApplication` y `validateManifest`.
