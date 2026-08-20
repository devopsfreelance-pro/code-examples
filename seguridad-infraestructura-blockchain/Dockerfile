# Imagen minima para correr el mock de RPC.
# En produccion real: fijar la imagen base por digest, no por tag (ver README).
FROM python:3.12-slim

WORKDIR /app
COPY mock_rpc_server.py .

# Usuario sin privilegios: el mismo principio de hardening que se aplica
# a un nodo blockchain real (nada corre como root si no es necesario).
RUN useradd --no-create-home --shell /usr/sbin/nologin rpcuser
USER rpcuser

ENTRYPOINT ["python3", "mock_rpc_server.py"]
CMD ["0.0.0.0", "8545"]
