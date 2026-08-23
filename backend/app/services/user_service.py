from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserRole
from app.auth.security import hash_password, verify_password


class UserService:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower().strip())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        db: AsyncSession,
        name: str,
        email: str,
        password: str,
        role: UserRole = UserRole.PATIENT,
        phone: Optional[str] = None,
    ) -> User:
        hashed = hash_password(password)
        user = User(
            name=name.strip(),
            email=email.lower().strip(),
            password_hash=hashed,
            role=role.value if isinstance(role, UserRole) else role,
            phone=phone.strip() if phone else None,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> Optional[User]:
        user = await UserService.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    async def list_users_by_role(
        db: AsyncSession,
        role: UserRole,
        limit: int = 100,
        offset: int = 0,
    ) -> List[User]:
        stmt = (
            select(User)
            .where(User.role == role.value if isinstance(role, UserRole) else role)
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
