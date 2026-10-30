from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings

settings = get_settings()

_engine = None
_async_session_maker = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            future=True,
        )
    return _engine


def get_session_maker():
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_maker


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with get_session_maker()() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def set_test_engine(test_engine):
    global _engine, _async_session_maker
    _engine = test_engine
    _async_session_maker = None
