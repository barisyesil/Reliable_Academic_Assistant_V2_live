import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpointEmbeddings # <-- İndiren değil, API'ye bağlanan modül
from langchain_pinecone import PineconeVectorStore

load_dotenv()

_vector_store = None

def get_vector_store() -> PineconeVectorStore:
    global _vector_store
    if _vector_store is None:
        raise RuntimeError("RAG servisi henüz başlatılmadı. Lifespan'ı kontrol et.")
    return _vector_store

def init_rag() -> PineconeVectorStore:
    global _vector_store
    
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise ValueError("[RAG] HATA: .env dosyasında HF_TOKEN bulunamadı!")

    print("[RAG] HuggingFace API üzerinden embedding modeline bağlanılıyor...")
    
    # DİKKAT: Artık modeli RAM'e indirmiyoruz!
    embeddings = HuggingFaceEndpointEmbeddings(
        model="BAAI/bge-m3",
        task="feature-extraction",
        huggingfacehub_api_token=hf_token
    )

    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    index_name = "estu-index"

    if not pinecone_api_key:
        raise ValueError("[RAG] HATA: .env dosyasında PINECONE_API_KEY bulunamadı!")

    print(f"[RAG] Pinecone Bulut Veritabanına bağlanılıyor (Index: {index_name})...")
    
    _vector_store = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings,
        pinecone_api_key=pinecone_api_key
    )
    
    print("[RAG] Pinecone Bulut bağlantısı BAŞARILI.")
    return _vector_store