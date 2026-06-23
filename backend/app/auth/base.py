from abc import ABC, abstractmethod


class AuthProvider(ABC):
    @abstractmethod
    async def authenticate(self, credentials: dict): ...

    @abstractmethod
    async def create_user(self, data: dict): ...
