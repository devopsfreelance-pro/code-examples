# Fase "Build" del ciclo de vida DevOps: empaqueta la app en un artefacto inmutable.
FROM python:3.12-slim

WORKDIR /app
COPY app.py .

ENV PORT=8080
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()" || exit 1

CMD ["python", "app.py"]
