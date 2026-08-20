#!/usr/bin/env python3
"""
Calculadora de decision AWS vs Azure vs GCP.

Implementa el framework de evaluacion ponderada descrito en el post
"AWS vs Azure vs GCP: Comparativa de los Gigantes del Cloud Computing".
Cada proveedor recibe un puntaje de 1 a 10 en varios criterios (costo,
performance, ecosistema, seguridad, innovacion, soporte, compliance).
Cada criterio tiene un peso, y el script calcula el puntaje final
ponderado para recomendar un proveedor.

Uso:
    python3 evaluate.py
    python3 evaluate.py --config config.yaml
    python3 evaluate.py --weight cost=0.4 --weight innovation=0.3
"""

import argparse
import sys

try:
    import yaml
except ImportError:
    print("Falta la dependencia PyYAML. Instalala con: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


class CloudProviderEvaluator:
    def __init__(self, criteria_weights):
        total = sum(criteria_weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"Los pesos de los criterios deben sumar 1.0 (suman {total:.2f})"
            )
        self.criteria_weights = criteria_weights

    def evaluate_provider(self, provider_scores):
        total_score = 0.0
        for criterion, weight in self.criteria_weights.items():
            score = provider_scores.get(criterion)
            if score is None:
                raise ValueError(f"Falta el criterio '{criterion}' en el proveedor")
            total_score += score * weight
        return total_score

    def rank_providers(self, providers):
        scores = {
            name: self.evaluate_provider(provider_scores)
            for name, provider_scores in providers.items()
        }
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return ranked


def parse_weight_overrides(pairs):
    overrides = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Formato invalido para --weight: '{pair}' (usar criterio=valor)")
        key, value = pair.split("=", 1)
        overrides[key.strip()] = float(value)
    return overrides


def print_table(ranked, weights):
    print("Pesos de criterios:")
    for criterion, weight in weights.items():
        print(f"  - {criterion:12s}: {weight:.2f}")
    print()
    print(f"{'Puesto':<7}{'Proveedor':<10}{'Puntaje ponderado':<20}")
    print("-" * 37)
    for i, (name, score) in enumerate(ranked, start=1):
        print(f"{i:<7}{name:<10}{score:<20.2f}")
    print()
    print(f"Proveedor recomendado: {ranked[0][0]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Ruta al archivo YAML con pesos y puntajes (default: config.yaml)",
    )
    parser.add_argument(
        "--weight",
        action="append",
        default=[],
        metavar="criterio=valor",
        help="Sobreescribe el peso de un criterio. Se puede repetir varias veces.",
    )
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    weights = dict(config["criteria_weights"])
    weights.update(parse_weight_overrides(args.weight))

    evaluator = CloudProviderEvaluator(weights)
    ranked = evaluator.rank_providers(config["providers"])
    print_table(ranked, weights)


if __name__ == "__main__":
    main()
