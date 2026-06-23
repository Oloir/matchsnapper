import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.base import AuthProvider
from app.models.user import User


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


class JWTAuthProvider(AuthProvider):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def authenticate(self, credentials: dict) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == credentials["email"])
        )
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            return None
        if not _verify_password(credentials["password"], user.hashed_password):
            return None
        return user

    async def create_user(self, data: dict) -> User:
        user = User(
            email=data["email"],
            username=data["username"],
            hashed_password=_hash_password(data["password"]),
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
