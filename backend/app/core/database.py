import ssl
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Supabase Pooler için ekstra ayarları belirliyoruz
connect_args = {
    "ssl": ctx,
    "statement_cache_size": 0,          # PgBouncer çakışmasını engeller
    "prepared_statement_cache_size": 0  # PgBouncer çakışmasını engeller
} if "sqlite" not in settings.DATABASE_URL else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True, # Kopan bağlantıları otomatik test edip yeniler (Bulut için şarttır)
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    from app.models.models import Base
    # Pooler üzerinden tablo oluşturma komutunu gönderiyoruz
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[DB] Supabase (IPv4 Pooler üzerinden) tablolar başarıyla oluşturuldu.")