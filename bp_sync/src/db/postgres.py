import uuid
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import false, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (  # declared_attr,
    DeclarativeBase,
    Mapped,
    mapped_column,
)

from core.settings import settings

engine = create_async_engine(
    settings.dsn,
    echo=settings.POSTGRES_DB_ECHO,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(AsyncAttrs, DeclarativeBase):  # type: ignore[misc]
    __abstract__ = True
    __allow_unmapped__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Уникальный идентификатор",
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        comment="Дата и время создания",
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата и время последнего обновления",
    )
    is_deleted_in_bitrix: Mapped[bool] = mapped_column(
        server_default=false(), default=False, comment="Удалён в Битрикс"
    )

    # @declared_attr.directive  # type: ignore
    # def __tablename__(cls) -> str:
    #    cls_name = cls.__name__.lower()
    #    return f"{cls_name}s"


async def create_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def purge_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()
