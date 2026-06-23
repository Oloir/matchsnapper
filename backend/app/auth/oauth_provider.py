from app.auth.base import AuthProvider


class OAuthProvider(AuthProvider):
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    async def authenticate(self, credentials: dict):
        raise NotImplementedError(f"OAuth via {self.provider_name} not implemented in MVP")

    async def create_user(self, data: dict):
        raise NotImplementedError(f"OAuth via {self.provider_name} not implemented in MVP")
