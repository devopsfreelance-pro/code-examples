FROM python:3.12-slim

WORKDIR /app
COPY app/app.py /app/app.py

ENV PORT=8080
ENV APP_ENVIRONMENT=production
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()" || exit 1

CMD ["python", "app.py"]
