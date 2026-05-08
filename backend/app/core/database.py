import ssl
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# SSL Ayarı: IPv4 üzerinden Pooler'a bağlanırken güvenliği sağlar
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    # Sadece sqlite değilse (yani supabase ise) SSL kullan
    connect_args={"ssl": ctx} if "sqlite" not in settings.DATABASE_URL else {}
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