# Wasm en infraestructura: servicio HTTP con Spin (Fermyon)

Ejemplo de código que acompaña al post [Wasm en infraestructura: Revolución en deployment moderno](https://www.devopsfreelance.pro/blog/posts/webassembly-wasm-infraestructura/).

## Qué demuestra

El post explica que WebAssembly permite compilar código (en este caso Rust) a un binario portable que arranca en milisegundos y pesa una fracción de lo que pesa una imagen de contenedor tradicional, usando frameworks como **Spin** de Fermyon para exponerlo como un microservicio HTTP.

Este ejemplo toma el snippet de Rust del post y lo convierte en un componente Wasm real, funcional, compilable y ejecutable en tu máquina:

- `src/lib.rs`: handler HTTP que compila a WebAssembly (target `wasm32-wasip1`) usando el SDK de Spin.
- `spin.toml`: manifiesto de la aplicación Spin (define el trigger HTTP y cómo compilar el componente).
- `compare_sizes.sh`: script que compara el tamaño del binario `.wasm` resultante contra una imagen Docker equivalente (`nginx:alpine`), para verificar en carne propia la afirmación del post de que los binarios wasm son 10-100x más chicos que las imágenes de contenedor.

## Requisitos

- [Rust](https://www.rust-lang.org/tools/install) (rustup) con el target `wasm32-wasip1`.
- [Spin CLI](https://developer.fermyon.com/spin/v2/install) de Fermyon (binario único, sin cuenta ni servicio pago).
- `curl` para probar el endpoint.
- Docker (opcional, solo para `compare_sizes.sh`).

No se usa ningún servicio cloud ni cuenta de terceros: todo corre localmente.

## Pasos para correrlo

1. Instalar el target de Rust para WASI:

```bash
rustup target add wasm32-wasip1
```

2. Instalar la Spin CLI (Linux/macOS):

```bash
curl -fsSL https://developer.fermyon.com/downloads/install.sh | bash
sudo mv spin /usr/local/bin/
```

3. Pararse en este directorio y compilar el componente wasm:

```bash
cd webassembly-wasm-infraestructura
spin build
```

Esto ejecuta internamente `cargo build --target wasm32-wasip1 --release` y genera `target/wasm32-wasip1/release/wasm_infra_demo.wasm`.

4. Levantar el servicio (Spin sirve el componente wasm en un runtime Wasmtime embebido):

```bash
spin up
```

5. En otra terminal, probar el endpoint:

```bash
curl -s http://127.0.0.1:3000/hola | python3 -m json.tool
```

Salida esperada:

```json
{
    "status": "healthy",
    "runtime": "wasm",
    "path": "/hola"
}
```

6. (Opcional) Comparar el tamaño del binario wasm contra una imagen de contenedor equivalente:

```bash
./compare_sizes.sh
```

Salida esperada (los valores exactos varían según versión de Rust/Docker):

```
== Tamano del binario Wasm ==
target/wasm32-wasip1/release/wasm_infra_demo.wasm: 245760 bytes (~240 KB)

== Tamano de una imagen Docker equivalente (nginx:alpine) ==
nginx:alpine: 44040192 bytes (~42 MB)

== Comparacion ==
La imagen de contenedor es aproximadamente 179x mas grande que el binario wasm.
```

7. Para detener el servicio, `Ctrl+C` en la terminal donde corre `spin up`.

## Notas

- El componente no requiere permisos de red ni de filesystem (`allowed_outbound_hosts = []` en `spin.toml`), en línea con el modelo de capabilities de WASI que describe el post.
- `spin up` arranca instantáneamente porque el bytecode wasm ya fue compilado; el "cold start" real (compilación JIT del wasm a código máquina) ocurre en microsegundos por request, no al iniciar el proceso `spin up`.
