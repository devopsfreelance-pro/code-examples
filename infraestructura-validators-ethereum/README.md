# Slashing protection para validadores de Ethereum

Ejemplo de código para el post [Infraestructura para validators de Ethereum: Guía completa](https://www.devopsfreelance.pro/blog/posts/infraestructura-validators-ethereum/).

## Qué demuestra

El post identifica el slashing como "el riesgo operativo número uno" y explica
la causa típica: doble firma por correr las mismas llaves en dos máquinas a
la vez (por ejemplo, un nodo de respaldo que arranca mientras el principal
solo tiene una partición de red, no está caído del todo).

Este ejemplo implementa en Python, de forma simplificada pero funcional, la
lógica que usa una base de "slashing protection" en formato
[EIP-3076](https://eips.ethereum.org/EIPS/eip-3076) (el mismo formato que
exportan/importan clientes reales con `lighthouse account validator
slashing-protection export/import`, mencionado en el post). El script recibe
un interchange file JSON con el historial de firmas de una llave y decide si
una nueva attestation o propuesta de bloque violaría alguna de las reglas de
slashing:

- **Doble voto**: dos attestations distintas para el mismo `target_epoch`.
- **Voto envolvente / envuelto** (surrounding vote): una attestation nueva
  que envuelve (o es envuelta por) un voto ya firmado.
- **Doble propuesta de bloque**: dos bloques distintos firmados para el
  mismo `slot`.

La idea es la misma que sostiene el mensaje del post: "un juego de llaves de
validador vive en un solo lugar". Si el mismo signing_root ya fue firmado,
el reintento es idempotente y se permite (por ejemplo, tras reiniciar el
validator client). Si aparece un signing_root distinto para el mismo
source/target/slot, es una señal de que dos procesos están firmando con la
misma llave y el script lo bloquea antes de que llegue a la red.

No reemplaza la slashing-protection DB real de Lighthouse/Teku/Prysm (esa
lógica tiene más casos borde y vive embebida en el cliente). Es una versión
didáctica para ver el mecanismo en código.

## Requisitos

- Python 3.8+ (sin dependencias externas, solo librería estándar)

## Cómo correrlo

```bash
cd infraestructura-validators-ethereum

# Escenario individual: attestation legítima (target epoch nuevo)
python3 slashing_protection.py sample_interchange.json check-attestation \
  --pubkey 0xa1d1ad0714035353258038e964ae9675dc0252ee22cea896825c01458e1807bfad2f9969338798548d9858a571f7f5 \
  --source-epoch 3006 \
  --target-epoch 3008 \
  --signing-root 0xnuevoroot001

# Escenario individual: doble voto (simula un nodo de respaldo firmando en paralelo)
python3 slashing_protection.py sample_interchange.json check-attestation \
  --pubkey 0xa1d1ad0714035353258038e964ae9675dc0252ee22cea896825c01458e1807bfad2f9969338798548d9858a571f7f5 \
  --source-epoch 2290 \
  --target-epoch 3007 \
  --signing-root 0xrootDIFERENTE-nodo-backup

# Los 4 escenarios juntos (legítimo, doble voto, voto envolvente, doble bloque)
chmod +x demo.sh
./demo.sh
```

## Salida esperada de `./demo.sh`

```
== Escenario 1: attestation legitima (target epoch mayor a la ultima firmada) ==
[PERMITIDO] attestation valida, no viola reglas de slashing

== Escenario 2: DOBLE VOTO -- mismo target epoch ya firmado, root distinto ==
   (simula un nodo de respaldo con las mismas llaves firmando en paralelo)
[BLOQUEADO] DOBLE VOTO: mismo source/target ya firmado con un signing_root distinto (dos procesos firmando la misma llave)

== Escenario 3: VOTO ENVOLVENTE -- intenta envolver la attestation ya firmada ==
[BLOQUEADO] VOTO ENVOLVENTE (surrounding vote): esta attestation envuelve un voto anterior

== Escenario 4: DOBLE PROPUESTA DE BLOQUE -- mismo slot ya firmado, root distinto ==
[BLOQUEADO] DOBLE PROPUESTA: mismo slot ya firmado con un signing_root distinto (dos procesos firmando la misma llave)

Escenarios 1 permitido; 2, 3 y 4 bloqueados. Ver README para el detalle.
```

`check-attestation` y `check-block` devuelven código de salida `0` cuando el
resultado es `PERMITIDO` y `1` cuando es `BLOQUEADO`, útil para engancharlo
en un script de migración real antes de arrancar el validator client en el
servidor nuevo.

## Archivos

- `slashing_protection.py`: carga el interchange file EIP-3076 y expone
  `check-attestation` / `check-block` por CLI.
- `sample_interchange.json`: interchange file de ejemplo con el historial de
  firmas de una llave (equivalente a lo que exporta
  `lighthouse account validator slashing-protection export`).
- `demo.sh`: corre los 4 escenarios contra el mismo archivo de ejemplo.

## Ir más allá

- En un cliente real, esta verificación corre en cada firma, no solo al
  migrar. El comando del post (`lighthouse vc --enable-doppelganger-protection`)
  agrega una segunda capa: escuchar la red unas épocas antes de firmar, por
  si otro proceso ya está usando la misma llave.
- No hay secretos ni cuentas reales involucradas: el pubkey y los
  signing_root de `sample_interchange.json` son valores de ejemplo, no
  corresponden a un validador en mainnet.
