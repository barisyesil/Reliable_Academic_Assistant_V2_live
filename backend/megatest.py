import socket
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def diagnose():
    # 1. TEST: DNS Çözümleme
    host = "db.dwmhdkorweaoslqtrkia.supabase.co"
    pooler_host = "aws-0-eu-central-1.pooler.supabase.com"
    
    print(f"--- 🔍 TEŞHİS BAŞLATILDI ---")
    
    for h in [host, pooler_host]:
        print(f"\n[*] {h} deneniyor...")
        try:
            # IPv4 ve IPv6 adreslerini almayı dene
            addresses = socket.getaddrinfo(h, None)
            for addr in addresses:
                print(f" [✓] Bulunan IP: {addr[4][0]} (Aile: {addr[0]})")
        except Exception as e:
            print(f" [X] DNS Çözülemedi: {e}")

    # 2. TEST: Doğrudan Port Erişimi (TCP)
    print(f"\n[*] Port 5432 (Direct) Erişimi:")
    s = socket.socket(socket.getaddrinfo(host, 5432)[0][0], socket.socket().type)
    s.settimeout(5)
    try:
        s.connect((host, 5432))
        print(" [✓] Port 5432 AÇIK (Bağlantı Başarılı)")
        s.close()
    except Exception as e:
        print(f" [X] Port 5432 KAPALI: {e}")

    # 3. TEST: asyncpg ile Manuel Bağlantı
    print(f"\n[*] asyncpg ile deneme...")
    try:
        # Şifreni ve URL'ini .env'den alıyoruz
        url = os.getenv("DATABASE_URL")
        conn = await asyncpg.connect(url, timeout=10)
        print(" [✓] asyncpg BAĞLANTISI BAŞARILI!")
        await conn.close()
    except Exception as e:
        print(f" [X] asyncpg HATASI: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose())