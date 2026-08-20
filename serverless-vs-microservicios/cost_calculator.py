#!/usr/bin/env python3
"""
Calculadora de costos: microservicios (AWS Fargate) vs serverless (AWS Lambda).

Reproduce con formulas de pricing reales (aprox., us-east-1, 2026) la
tabla de costos del post "Serverless vs Microservicios": a bajo trafico
serverless es mas barato, a trafico alto y constante los contenedores
siempre encendidos se vuelven mas eficientes.

Uso:
    python3 cost_calculator.py <requests_por_mes> [duracion_ms] [memoria_mb] [replicas_fargate]

Ejemplo:
    python3 cost_calculator.py 1000000
    python3 cost_calculator.py 100000000 150 512 3
"""
import sys

# --- Precios de referencia AWS us-east-1 (aprox., por si cambian: son
# solo para ilustrar la comparacion, no para facturacion real) ---
LAMBDA_PRICE_PER_REQUEST = 0.0000002          # USD por request
LAMBDA_PRICE_PER_GB_SECOND = 0.0000166667     # USD por GB-segundo
LAMBDA_FREE_REQUESTS = 1_000_000              # free tier mensual

FARGATE_PRICE_PER_VCPU_HOUR = 0.04048         # USD por vCPU-hora
FARGATE_PRICE_PER_GB_HOUR = 0.004445          # USD por GB-hora
HOURS_PER_MONTH = 730


def lambda_monthly_cost(requests_per_month: int, duration_ms: float, memory_mb: int) -> float:
    """Costo mensual de Lambda: pago por invocacion + pago por GB-segundo consumido."""
    billable_requests = max(requests_per_month - LAMBDA_FREE_REQUESTS, 0)
    request_cost = billable_requests * LAMBDA_PRICE_PER_REQUEST

    gb_seconds = requests_per_month * (duration_ms / 1000) * (memory_mb / 1024)
    compute_cost = gb_seconds * LAMBDA_PRICE_PER_GB_SECOND

    return request_cost + compute_cost


def fargate_monthly_cost(replicas: int, vcpu: float, memory_gb: float) -> float:
    """Costo mensual de Fargate: contenedores siempre encendidos, 730h/mes cada uno."""
    vcpu_cost = replicas * vcpu * FARGATE_PRICE_PER_VCPU_HOUR * HOURS_PER_MONTH
    memory_cost = replicas * memory_gb * FARGATE_PRICE_PER_GB_HOUR * HOURS_PER_MONTH
    return vcpu_cost + memory_cost


def recommend(lambda_cost: float, fargate_cost: float, requests_per_month: int) -> str:
    if lambda_cost < fargate_cost:
        diff_pct = (fargate_cost - lambda_cost) / fargate_cost * 100 if fargate_cost else 0
        return (f"Serverless es ~{diff_pct:.0f}% mas barato a este volumen "
                f"({requests_per_month:,} req/mes).")
    diff_pct = (lambda_cost - fargate_cost) / lambda_cost * 100 if lambda_cost else 0
    return (f"Microservicios en contenedores son ~{diff_pct:.0f}% mas baratos "
            f"a este volumen ({requests_per_month:,} req/mes). "
            "El costo fijo de los contenedores siempre encendidos ya se amortiza.")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    requests_per_month = int(args[0])
    duration_ms = float(args[1]) if len(args) > 1 else 100.0
    memory_mb = int(args[2]) if len(args) > 2 else 256
    replicas = int(args[3]) if len(args) > 3 else 2

    # Fargate: perfil equivalente al deployment del post (0.5 vCPU, 512Mi por replica)
    vcpu = 0.5
    memory_gb = 0.5

    l_cost = lambda_monthly_cost(requests_per_month, duration_ms, memory_mb)
    f_cost = fargate_monthly_cost(replicas, vcpu, memory_gb)

    print(f"Trafico simulado: {requests_per_month:,} requests/mes")
    print(f"Lambda:    duracion={duration_ms}ms, memoria={memory_mb}MB")
    print(f"Fargate:   {replicas} replicas x {vcpu} vCPU / {memory_gb}GB, siempre encendidas")
    print()
    print(f"  Costo mensual Lambda (serverless):        ${l_cost:,.2f}")
    print(f"  Costo mensual Fargate (microservicios):   ${f_cost:,.2f}")
    print()
    print(recommend(l_cost, f_cost, requests_per_month))


if __name__ == "__main__":
    main()
