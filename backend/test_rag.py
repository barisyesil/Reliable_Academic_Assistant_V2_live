from app.services.rag_service import init_rag, get_vector_store
from dotenv import load_dotenv
load_dotenv()

def test_search():
    print("[*] RAG Servisi başlatılıyor...")
    vector_store = init_rag()
    
    query = "staj yerleri" # Senin logunda aranan kelime
    print(f"[*] '{query}' için arama yapılıyor...")
    
    # En yakın 2 sonucu getir
    results = vector_store.similarity_search(query, k=2)
    
    if results:
        print(f"\n[✓] BAŞARILI! {len(results)} sonuç bulundu.")
        for i, doc in enumerate(results):
            print(f"\nSonuç {i+1}:")
            print(f"Kaynak: {doc.metadata.get('document_name', 'Bilinmiyor')}")
            print(f"İçerik Özeti: {doc.page_content[:150]}...")
    else:
        print("\n[X] HATA: Hiç sonuç bulunamadı. Veritabanı boş olabilir!")

if __name__ == "__main__":
    test_search()