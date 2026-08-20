# FinOps: mini motor de análisis de costos + policy de tagging

Ejemplo de código para el post [FinOps: Guía Completa de Optimización Financiera en Cloud](https://www.devopsfreelance.pro/blog/posts/finops-optimizacion-financiera-cloud/).

## Qué demuestra este ejemplo

El post cubre el ciclo **Informar → Optimizar → Operar** de FinOps. Este ejemplo
implementa en miniatura las dos primeras fases, sin necesitar una cuenta de AWS:

1. **`analyze_costs.py`**: lee un export de costos (simula el AWS Cost & Usage
   Report / Cost Explorer) y aplica reglas típicas de un Centro de Excelencia
   FinOps:
   - Calcula cobertura de etiquetado y detecta recursos sin `environment` o
     `cost_center` (bloquean el chargeback/showback).
   - Agrupa el gasto diario por ambiente y por cost center.
   - Detecta volúmenes EBS huérfanos (candidatos a eliminación directa).
   - Marca instancias con CPU baja como candidatas a right-sizing y estima el
     ahorro mensual.
2. **`tagging_policy.tf`**: la política de IAM en Terraform del post que
   deniega `ec2:RunInstances` si faltan las tags `Environment` o `CostCenter`
   (la base técnica de la fase "Informar" para poder atribuir costos).
3. **`sample_cost_data.csv`**: dataset de ejemplo con 13 recursos (EC2, RDS,
   S3, EBS, EKS) con mezcla intencional de recursos bien etiquetados, sin
   etiquetar, huérfanos y con baja utilización, para que el script tenga algo
   interesante que reportar.

## Requisitos

- Python 3.8+ (solo librería estándar, sin `pip install`).
- Terraform >= 1.5 (opcional, solo si querés validar `tagging_policy.tf`; no
  hace falta cuenta de AWS, `terraform validate` no requiere credenciales).

## Cómo correrlo

### 1. Análisis de costos

```bash
cd finops-optimizacion-financiera-cloud
python3 analyze_costs.py sample_cost_data.csv
```

Opcional, ajustar el umbral de CPU para right-sizing (default 15%):

```bash
python3 analyze_costs.py sample_cost_data.csv --utilization-threshold 20
```

**Salida esperada** (resumen, la salida completa incluye el detalle por recurso):

```
============================================================
FASE 1: INFORMAR - Visibilidad y asignación de costos
============================================================
Gasto diario total analizado: USD 768.40
Gasto mensual proyectado (x30): USD 23,052.00
...
Cobertura de etiquetado: 46.2% (6/13 recursos)
...
============================================================
FASE 2: OPTIMIZAR - Right-sizing y recursos huérfanos
============================================================
Volúmenes EBS huérfanos detectados: 2 (USD 19.60/día = USD 588.00/mes)
...
Candidatos a right-sizing (CPU < 15%): 5
...
============================================================
RESUMEN EJECUTIVO
============================================================
Oportunidad de ahorro mensual identificada: USD 3,679.50
  - Eliminación de huérfanos:  USD 588.00/mes
  - Right-sizing:              USD 3,091.50/mes
Esto representa el 16.0% del gasto mensual proyectado.
```

Para usarlo con datos reales, exportá el AWS Cost & Usage Report (o el
resultado de `get_cost_and_usage` de boto3) a un CSV con las mismas columnas
que `sample_cost_data.csv` y corré el script contra ese archivo.

### 2. Validar la política de tagging en Terraform

```bash
cd finops-optimizacion-financiera-cloud
terraform init -backend=false
terraform validate
```

**Salida esperada**:

```
Success! The configuration is valid.
```

`terraform validate` solo revisa sintaxis y coherencia del código, no requiere
credenciales de AWS ni crea recursos. Para aplicarla de verdad hace falta una
cuenta AWS con permisos IAM (`aws configure` con credenciales propias) y
correr `terraform plan` / `terraform apply`.

## Notas

- No se incluyen credenciales ni cuentas de AWS: todo corre en local con datos
  de muestra.
- `analyze_costs.py` no tiene dependencias externas (no requiere `pip
  install`), a propósito, para que sea copiar y correr.
