# Checkpoint synchronization en Ethereum: demo ejecutable

Post relacionado: [Guía definitiva de checkpoint synchronization en Ethereum](https://www.devopsfreelance.pro/blog/posts/checkpoint-synchronization-ethereum/)

## Qué demuestra este ejemplo

El post explica que un nodo Ethereum puede sincronizar de dos maneras:

- **Full sync**: procesa y verifica el estado de la cadena bloque por bloque, desde el bloque génesis hasta la cabeza actual.
- **Checkpoint sync**: confía en un checkpoint reciente (finalizado y distribuido por un proveedor de checkpoints o por la propia red) y solo procesa el estado de los bloques posteriores a ese checkpoint.

Reproducir esto contra un nodo `geth` real requiere descargar la blockchain de Ethereum (cientos de GB) o depender de un checkpoint provider externo, algo que no es viable para un ejemplo que se corre en minutos. Este ejemplo simula el mecanismo con una cadena de bloques de juguete (Python puro, sin dependencias externas):

1. `generate_chain.py` genera una cadena de 1500 bloques encadenados por hash y guarda un **checkpoint confiable** en el bloque #1400 (`checkpoint.json`), tal como lo publicaría un proveedor de checkpoints.
2. `sync_demo.py` sincroniza la misma cadena de dos formas y mide el tiempo:
   - `full_sync()`: valida el enlace y el "estado" (trabajo de CPU simulado) de los 1500 bloques, desde el génesis.
   - `checkpoint_sync()`: valida que el checkpoint coincide con la cadena y luego solo procesa el estado de los ~100 bloques posteriores al checkpoint.

El resultado deja ver, con números reales, por qué checkpoint sync reduce drásticamente el trabajo de sincronización: en este ejemplo el checkpoint sync es más de 10x más rápido porque evita re-ejecutar el estado del 93% de la historia de la cadena.

## Requisitos

- Python 3.8 o superior (sin librerías externas, todo con la stdlib).

## Cómo correrlo

```bash
cd checkpoint-synchronization-ethereum

# 1. Genera la cadena de juguete y el checkpoint confiable
python3 generate_chain.py

# 2. Corre la comparación full sync vs checkpoint sync
python3 sync_demo.py
```

## Salida esperada

```
Generando cadena de 1500 bloques (puede tardar unos segundos)...
Cadena guardada en chain.json (1500 bloques).
Checkpoint guardado en checkpoint.json (bloque #1400).
Bloque genesis esperado: 0000000000000000000000000000000000000000000000000000000000000000

Cadena cargada: 1500 bloques. Checkpoint en bloque #1400.

[full sync]       bloques verificados:  1500  tiempo: 14.91s
[checkpoint sync] bloques verificados:   100  tiempo: 0.95s

Checkpoint sync fue 15.6x mas rapido que full sync
y solo tuvo que re-ejecutar el estado de 100 bloques en vez de los 1500 bloques completos del historial.
```

Los tiempos exactos varían según la CPU, pero la relación se mantiene: checkpoint sync siempre verifica muchos menos bloques (y tarda muchas veces menos) que full sync, porque parte de un estado ya confiado en lugar de reconstruirlo desde el génesis.

## Archivos

- `chain_lib.py`: librería con el modelo de bloque, minado simplificado (PoW con dificultad baja), y la función `expensive_state_check` que simula el costo de reconstruir el estado de un bloque.
- `generate_chain.py`: genera `chain.json` (la cadena) y `checkpoint.json` (el checkpoint confiable en el bloque #1400).
- `sync_demo.py`: ejecuta y compara `full_sync()` vs `checkpoint_sync()`, imprimiendo tiempos y cantidad de bloques verificados.

## Llevarlo a un nodo real

Para probar checkpoint synchronization con un cliente Ethereum real (fuera del alcance de este ejemplo por el tamaño de la descarga), el flujo equivalente en `geth` es:

```bash
geth --syncmode "snap" \
     --checkpoint-provider "https://checkpoint-sync.example.org" \
     --http --http.api eth,net,engine,admin
```

Reemplazá `--checkpoint-provider` por un proveedor de checkpoints real y confiable de la red que uses (mainnet, testnet, etc.); no hay un valor único válido para todos los casos, por eso se documenta acá en vez de hardcodearlo en el ejemplo.
