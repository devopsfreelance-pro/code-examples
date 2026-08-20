# GDPR compliance en infraestructura cloud - ejemplo ejecutable

Post relacionado: [GDPR en infraestructura cloud](https://www.devopsfreelance.pro/blog/posts/gdpr-infraestructura-cloud/)

## Que demuestra este ejemplo

El post describe tres controles tecnicos centrales para cumplir GDPR en
sistemas cloud: cifrado selectivo de datos personales (PII), anonimizacion
de identificadores (IP, user-agent) y auditoria de cada acceso a datos
personales. Este ejemplo implementa esos tres controles en un script
Python autocontenido, sin depender de Azure Key Vault ni de ningun
servicio externo:

- `gdpr_demo.py` cifra los campos sensibles de un registro (`email`,
  `phone`, `address`) con `cryptography.Fernet`, usando una clave local
  que simula lo que en produccion seria un KMS/Key Vault.
- Anonimiza `ip_address` y `user_agent` mediante hash SHA-256, preservando
  utilidad analitica sin retener el dato identificable original.
- Registra cada operacion de cifrado/descifrado en `audit.log` (formato
  JSON lines) con timestamp, sujeto y campos tocados, ilustrando el
  registro de actividades de procesamiento que exige el articulo 30.

Ademas se incluye `gdpr-audit-policy.yaml`, la politica de auditoria de
Kubernetes citada en el post, para quien quiera validarla contra un
cluster local (kind/minikube).

## Requisitos

- Python 3.10+ (usa sintaxis `list[str]`)
- pip
- Opcional, solo para validar el manifiesto de Kubernetes: `kubectl` o
  `python3 -c "import yaml"` (PyYAML)

## Pasos para correrlo

```bash
cd gdpr-infraestructura-cloud

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python3 gdpr_demo.py
```

### Salida esperada

```
=== Registro original ===
{
  "user_id": "user-4821",
  "email": "maria.gonzalez@example.com",
  "phone": "+34-600-123-456",
  "address": "Calle Mayor 10, Madrid, España",
  "ip_address": "203.0.113.42",
  "user_agent": "Mozilla/5.0 (X11; Linux x86_64)",
  "plan": "premium"
}

=== Registro cifrado + IP/UA anonimizados (listo para almacenar) ===
{
  "user_id": "user-4821",
  "email": "gAAAAA...",
  "phone": "gAAAAA...",
  "address": "gAAAAA...",
  "ip_address": "9f1c2a7b3e4d5f6a",
  "user_agent": "3a2b1c0d9e8f7a6b",
  "plan": "premium",
  "_encrypted_at": "2026-08-20T..."
}

=== Registro descifrado (acceso autorizado) ===
{
  "user_id": "user-4821",
  "email": "maria.gonzalez@example.com",
  ...
}

=== Log de auditoria (audit.log) ===
{"timestamp": "...", "action": "encrypt", "subject_id": "user-4821", "fields": ["email", "phone", "address"]}
{"timestamp": "...", "action": "decrypt", "subject_id": "user-4821", "fields": ["email", "phone", "address"]}

OK: cifrado/descifrado y anonimizacion consistentes.
```

Los valores cifrados (`gAAAAA...`) y los hashes de IP/user-agent varian
en cada corrida porque Fernet usa un IV aleatorio; el script valida con
`assert` que el ciclo cifrado/descifrado es consistente y que el campo
no sensible (`plan`) nunca se toca.

El script genera dos archivos en este mismo directorio, que no se
versionan (ver `.gitignore`):

- `gdpr_demo.key`: clave Fernet local (simula el secreto que en
  produccion vive en un KMS/Key Vault, nunca en el repo).
- `audit.log`: log de auditoria en JSON lines, se reinicia en cada
  corrida para que la demo sea reproducible.

## Validar la politica de auditoria de Kubernetes (opcional)

Sin necesidad de un cluster, solo para chequear que el YAML es valido:

```bash
python3 -c "import yaml,sys; yaml.safe_load(open('gdpr-audit-policy.yaml'))" && echo "YAML valido"
```

Para probarla contra un cluster real hace falta pasarla como
`--audit-policy-file` al `kube-apiserver` (por ejemplo con `kind`
montando el archivo y configurando `extraArgs`); queda fuera del alcance
de esta demo minima porque requiere reconfigurar el control plane.

## No hay secretos reales

No se usan credenciales de ningun proveedor cloud. La clave de cifrado
es generada localmente por el propio script y sirve solo para esta
demo.
