#!/usr/bin/env python3
"""
Matriz de decision interactiva: microservicios vs serverless.

Operacionaliza la tabla "Matriz de Decision" del post: hace las mismas
preguntas y calcula un puntaje para recomendar una arquitectura.

Uso:
    python3 decision_matrix.py            # modo interactivo
    python3 decision_matrix.py --demo     # corre con respuestas de ejemplo (sin input)
"""
import sys

QUESTIONS = [
    ("trafico_constante", "Trafico constante > 10K req/min?", "microservicios"),
    ("procesos_largos", "Procesos > 15 minutos?", "microservicios"),
    ("websockets", "Necesitas WebSockets?", "microservicios"),
    ("equipo_devops", "Equipo DevOps dedicado?", "microservicios"),
    ("trafico_variable", "Trafico variable o esporadico?", "serverless"),
    ("event_driven", "Event-driven processing?", "serverless"),
    ("equipo_chico", "Equipo pequeno sin infra?", "serverless"),
    ("time_to_market", "Time-to-market es prioridad?", "serverless"),
    ("multi_cloud", "Multi-cloud obligatorio?", "microservicios"),
    ("presupuesto_bajo", "Presupuesto ajustado, bajo uso?", "serverless"),
]

# Respuestas de ejemplo para --demo: equipo chico, trafico variable, sin DevOps dedicado
DEMO_ANSWERS = {
    "trafico_constante": False,
    "procesos_largos": False,
    "websockets": False,
    "equipo_devops": False,
    "trafico_variable": True,
    "event_driven": True,
    "equipo_chico": True,
    "time_to_market": True,
    "multi_cloud": False,
    "presupuesto_bajo": True,
}


def ask(prompt: str) -> bool:
    resp = input(f"{prompt} [s/N]: ").strip().lower()
    return resp in ("s", "si", "y", "yes")


def score(answers: dict) -> tuple:
    micro_score = 0
    serverless_score = 0
    for key, _prompt, side in QUESTIONS:
        if answers.get(key):
            if side == "microservicios":
                micro_score += 1
            else:
                serverless_score += 1
    return micro_score, serverless_score


def recommend(micro_score: int, serverless_score: int) -> str:
    if micro_score == serverless_score:
        return ("Empate. Considera un patron hibrido: core de negocio en "
                "microservicios, funciones auxiliares (auth, notificaciones, "
                "procesamiento de eventos) en serverless.")
    if micro_score > serverless_score:
        return f"Recomendacion: microservicios en contenedores ({micro_score} vs {serverless_score})."
    return f"Recomendacion: serverless ({serverless_score} vs {micro_score})."


def main():
    demo = "--demo" in sys.argv

    answers = {}
    if demo:
        answers = DEMO_ANSWERS
        print("Modo demo (respuestas de ejemplo: equipo chico, trafico variable):\n")
        for key, prompt, _side in QUESTIONS:
            print(f"  {prompt} [s/N]: {'s' if answers[key] else 'n'}")
    else:
        print("Respondé s/N a cada pregunta:\n")
        for key, prompt, _side in QUESTIONS:
            answers[key] = ask(prompt)

    micro_score, serverless_score = score(answers)

    print()
    print(f"Puntaje microservicios: {micro_score}/10")
    print(f"Puntaje serverless:     {serverless_score}/10")
    print()
    print(recommend(micro_score, serverless_score))


if __name__ == "__main__":
    main()
