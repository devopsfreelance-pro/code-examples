"""
Mini implementacion de un cliente de feature flags.

Ilustra el concepto central del post: separar el DESPLIEGUE del codigo
de la LIBERACION de la funcionalidad, mediante:

  - Un "servicio" de flags centralizado (aqui: un archivo JSON, en un
    sistema real seria LaunchDarkly, Split.io, Unleash, etc.)
  - Rollout progresivo por porcentaje (0-100%)
  - "Sticky bucketing": un mismo user_id siempre cae en la misma
    variante, via hash determinista (no random en cada request)
  - Cache en memoria con recarga periodica (simula el patron de
    polling que describe el post como fallback de streaming/websockets)
"""

import hashlib
import json
import time
from pathlib import Path


class FeatureFlagClient:
    def __init__(self, config_path: str = "flags.json", cache_ttl_seconds: float = 5.0):
        self.config_path = Path(config_path)
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict = {}
        self._cache_loaded_at: float = 0.0
        self._load_flags(force=True)

    def _load_flags(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and (now - self._cache_loaded_at) < self.cache_ttl_seconds:
            return  # cache aun valido, no golpeamos el "servicio"

        if not self.config_path.exists():
            raise FileNotFoundError(f"No se encontro el archivo de flags: {self.config_path}")

        with self.config_path.open("r", encoding="utf-8") as fh:
            self._cache = json.load(fh)
        self._cache_loaded_at = now

    def _bucket_for(self, flag_name: str, user_id: str) -> int:
        """Hash deterministico -> numero estable 0-99 para (flag, usuario).

        Sticky bucketing: el mismo usuario siempre obtiene el mismo bucket
        para el mismo flag, sesion tras sesion.
        """
        key = f"{flag_name}:{user_id}".encode("utf-8")
        digest = hashlib.sha256(key).hexdigest()
        return int(digest[:8], 16) % 100

    def is_enabled(self, flag_name: str, user_id: str) -> bool:
        self._load_flags()

        flag = self._cache.get(flag_name)
        if flag is None:
            # Flag desconocido: fail-safe, se comporta como apagado.
            return False

        if not flag.get("enabled", False):
            return False

        rollout = flag.get("rollout_percentage", 0)
        if rollout >= 100:
            return True
        if rollout <= 0:
            return False

        return self._bucket_for(flag_name, user_id) < rollout

    def all_flags(self) -> dict:
        self._load_flags()
        return dict(self._cache)
