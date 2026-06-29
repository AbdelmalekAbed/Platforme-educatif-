from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    # Neon free tier suspend le compute après ~5 min : une connexion gardée en pool
    # devient morte. pool_pre_ping teste la connexion (et réveille Neon proprement)
    # avant chaque emprunt ; pool_recycle la jette au bout de 5 min pour éviter de
    # tomber sur une socket coupée. statement_cache_size=0 reste obligatoire (PgBouncer).
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0},
)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
