#!/usr/bin/env python3
"""
Exportador Prometheus que simula las metricas de un nodo Ethereum L2
(OP Stack / op-node) descritas en el post del blog:

  - l2_unsafe_head / l2_safe_head: altura del ultimo bloque L2 vs. el
    ultimo bloque L2 confirmado en L1 (safe head). La diferencia entre
    ambos es el "sync lag" que dispara la alerta L2SyncLag.
  - l2_last_batch_submission_timestamp: momento del ultimo batch
    publicado en L1. Si pasa mucho tiempo sin publicar, dispara
    L2BatchSubmissionDelay.
  - l2_p2p_peer_count: peers P2P conectados. Pocos peers dispara
    L2PeerCount.

No requiere ningun nodo real ni RPC externo: es un simulador didactico
para poder ejercitar localmente las reglas de alerting de Prometheus
que aparecen en el post.
"""
import http.server
import socketserver
import time

PORT = 9101
START = time.time()

# El "safe head" se queda deliberadamente atras del "unsafe head" para
# que, pasados ~100 bloques de diferencia, la regla L2SyncLag pase a
# estado "pending" en Prometheus (expr > 100).
UNSAFE_BLOCKS_PER_SEC = 2.0
SAFE_BLOCKS_PER_SEC = 1.7

# Ultimo batch publicado en L1 hace mas de 3600s dispara
# L2BatchSubmissionDelay. Lo dejamos fijo en el arranque del proceso
# para que la alerta pase a "pending" apenas pasa 1h de uptime del
# contenedor (se puede forzar antes bajando el valor del expr al
# probar, ver README).
LAST_BATCH_SUBMISSION = START

# Peers por debajo de 3 dispara L2PeerCount. Se fija en 2 para que la
# alerta este siempre en pending y sirva de ejemplo.
PEER_COUNT = 2


class MetricsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        elapsed = time.time() - START
        unsafe_head = int(1_000_000 + elapsed * UNSAFE_BLOCKS_PER_SEC)
        safe_head = int(1_000_000 + elapsed * SAFE_BLOCKS_PER_SEC)

        body = (
            "# HELP l2_unsafe_head Ultimo bloque L2 producido por el sequencer\n"
            "# TYPE l2_unsafe_head gauge\n"
            f"l2_unsafe_head {unsafe_head}\n"
            "# HELP l2_safe_head Ultimo bloque L2 confirmado (derivado) desde L1\n"
            "# TYPE l2_safe_head gauge\n"
            f"l2_safe_head {safe_head}\n"
            "# HELP l2_last_batch_submission_timestamp Unix timestamp del ultimo batch publicado en L1\n"
            "# TYPE l2_last_batch_submission_timestamp gauge\n"
            f"l2_last_batch_submission_timestamp {LAST_BATCH_SUBMISSION}\n"
            "# HELP l2_p2p_peer_count Peers P2P conectados al nodo L2\n"
            "# TYPE l2_p2p_peer_count gauge\n"
            f"l2_p2p_peer_count {PEER_COUNT}\n"
        )

        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        pass  # silencia el log de acceso por request


if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), MetricsHandler) as httpd:
        print(f"Mock L2 exporter escuchando en :{PORT}/metrics")
        httpd.serve_forever()
