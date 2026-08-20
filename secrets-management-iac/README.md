# Secrets Management en IaC: cifrado dentro del repo con SOPS + age

Ejemplo ejecutable del post: [Secrets Management en IaC: Guía Completa para Infraestructura como Código](https://www.devopsfreelance.pro/blog/posts/secrets-management-iac/)

## Qué demuestra

El post explica el enfoque GitOps de la sección "SOPS: secretos cifrados dentro
del repo": el secreto SÍ vive en el repositorio, pero cifrado, y solo quien
tiene la clave puede descifrarlo, dejando las claves del YAML legibles para
que el diff siga siendo útil.

Este ejemplo lo reproduce completo y localmente, sin cloud ni cuentas:

1. Genera un par de claves **age** (la clave privada nunca sale de tu máquina).
2. Cifra `demo-values.plain.yaml` con **SOPS** usando la clave pública age,
   generando `demo-values.enc.yaml` (esto es lo único que se comitearía a git).
3. Descifra `demo-values.enc.yaml` con la clave privada, tal como haría un
   desarrollador con acceso o un pipeline de CI, y recupera los valores
   originales.

Así se ve en la práctica la frase central del post: "el código declara dónde
está el secreto, no cuál es"; acá el archivo cifrado es comiteable tal cual,
y el valor real solo aparece en memoria en el momento del `decrypt`.

No cubre Vault, External Secrets Operator ni OIDC (esos escenarios requieren
infraestructura cloud o un cluster; hay ejemplos dedicados a Vault en
`../hashicorp-vault-gestion-secretos/` y `../gestion-secretos/`). El foco acá
es específicamente SOPS, que ningún otro ejemplo del repo cubre todavía.

## Requisitos

- Linux x86_64 (los comandos de instalación de abajo son para esa arquitectura;
  para macOS/Windows o ARM, bajar el binario correspondiente desde los releases).
- `curl` y `tar` para instalar los binarios.
- `bash`.

No requiere Docker, Kubernetes ni cuenta de ningún cloud.

### Instalar age y sops (si no los tenés)

```bash
# age (genera el par de claves)
sudo apt-get update && sudo apt-get install -y age

# sops (binario oficial, ejemplo v3.9.1 para Linux amd64)
curl -LO https://github.com/getsops/sops/releases/download/v3.9.1/sops-v3.9.1.linux.amd64
chmod +x sops-v3.9.1.linux.amd64
sudo mv sops-v3.9.1.linux.amd64 /usr/local/bin/sops

# Verificar
age-keygen --version
sops --version
```

## Archivos

- `demo-values.plain.yaml`: archivo de ejemplo en texto plano (valores
  ficticios). Es el insumo de `encrypt.sh`; en un repo real este archivo
  jamás se comitea.
- `encrypt.sh`: genera la clave age local (si no existe) y cifra
  `demo-values.plain.yaml` con SOPS, generando `demo-values.enc.yaml`.
- `decrypt.sh`: usa la clave privada local para descifrar
  `demo-values.enc.yaml` y muestra los valores originales.

Al correr `encrypt.sh` se crean además (no versionados, son salida de la demo):

- `keys/age-key.txt`: el par de claves age generado localmente. **Nunca se
  comitea a git**; es el equivalente de la clave que en un equipo real
  guardarían de forma segura (KMS, gestor de secretos del CI, etc.).
- `demo-values.enc.yaml`: el archivo cifrado. Este sí es seguro de comitear.

## Pasos para correrlo

```bash
cd secrets-management-iac

# 1. Cifrar el archivo de ejemplo
./encrypt.sh

# 2. Inspeccionar el archivo cifrado (esto es lo que iria a git)
cat demo-values.enc.yaml

# 3. Descifrar y verificar que los valores coinciden con demo-values.plain.yaml
./decrypt.sh

# 4. Limpieza (borra la clave y el archivo cifrado generados por la demo)
rm -rf keys demo-values.enc.yaml
```

## Salida esperada

Al correr `./encrypt.sh`:

```
==> Generando par de claves age (solo para este demo local)
==> Clave publica age: age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
==> Cifrando .../demo-values.plain.yaml -> .../demo-values.enc.yaml

==> Listo.
    - demo-values.enc.yaml es seguro de comitear a git (valores cifrados).
    - demo-values.plain.yaml y keys/ NUNCA se comitean.

Vista previa del archivo cifrado:
db_password: ENC[AES256_GCM,data:Xk9f2...,tag:h8Qw...,type:str]
api_key: ENC[AES256_GCM,data:9mPz1...,tag:r2Lp...,type:str]
sops:
    age:
        - recipient: age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          enc: ...
    ...
```

Al correr `./decrypt.sh`:

```
==> Descifrando .../demo-values.enc.yaml con la clave privada local
db_password: S3cr3tP4ss!Demo
api_key: demo-api-key-0123456789
```

Los valores decrypted coinciden exactamente con `demo-values.plain.yaml`,
confirmando el ciclo completo: texto plano -> cifrado (comiteable) ->
texto plano (solo con la clave correcta).

## Nota de seguridad

`S3cr3tP4ss!Demo` y `demo-api-key-0123456789` son valores ficticios solo para
este demo local. `keys/age-key.txt` que genera `encrypt.sh` es una clave real
de age: no la reutilices fuera de este ejercicio y borrala con el paso de
limpieza de arriba. En un equipo real, la clave privada age (o la KMS key que
la reemplaza) se guarda en un gestor de secretos del CI o en la máquina de
cada operador, nunca en el repositorio.
