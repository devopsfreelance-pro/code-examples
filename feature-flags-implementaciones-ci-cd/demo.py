"""
Demo ejecutable: simula el UserService del post y mide, con trafico
simulado, que el rollout progresivo y el sticky bucketing funcionan
como se describe en el articulo.
"""

from feature_flags import FeatureFlagClient


class UserService:
    def __init__(self, flag_client: FeatureFlagClient):
        self.flag_client = flag_client

    def get_user_dashboard(self, user_id: str) -> dict:
        if self.flag_client.is_enabled("new-dashboard-design", user_id):
            return self.render_new_dashboard(user_id)
        return self.render_legacy_dashboard(user_id)

    def render_new_dashboard(self, user_id: str) -> dict:
        return {"user_id": user_id, "version": "v2", "features": ["analytics", "widgets"]}

    def render_legacy_dashboard(self, user_id: str) -> dict:
        return {"user_id": user_id, "version": "v1", "features": ["basic"]}


def main() -> None:
    client = FeatureFlagClient(config_path="flags.json")
    service = UserService(client)

    print("=== Flags cargados desde flags.json ===")
    for name, flag in client.all_flags().items():
        print(f"  {name}: enabled={flag['enabled']} rollout={flag['rollout_percentage']}% - {flag['description']}")

    n_users = 2000
    v2_count = 0
    for i in range(n_users):
        user_id = f"user-{i}"
        result = service.get_user_dashboard(user_id)
        if result["version"] == "v2":
            v2_count += 1

    pct = (v2_count / n_users) * 100
    print(f"\n=== Rollout observado: new-dashboard-design ===")
    print(f"  {v2_count}/{n_users} usuarios ({pct:.1f}%) ven la v2")
    print(f"  Configurado en flags.json: 25% -> esperado ~25% (hash uniforme)")

    print("\n=== Sticky bucketing: mismo usuario, misma variante siempre ===")
    for user_id in ("user-1", "user-1", "user-1"):
        result = service.get_user_dashboard(user_id)
        print(f"  {user_id} -> version {result['version']}")

    print("\n=== Kill switch: ops toggle apagado ===")
    print(f"  maintenance-mode enabled para user-1: {client.is_enabled('maintenance-mode', 'user-1')}")


if __name__ == "__main__":
    main()
