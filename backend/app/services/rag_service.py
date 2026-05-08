import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

load_dotenv()
_vector_store = None

def get_vector_store() -> PineconeVectorStore:
    global _vector_store
    if _vector_store is None:
        raise RuntimeError("RAG servisi henüz başlatılmadı. Lifespan'ı kontrol et.")
    return _vector_store

def init_rag() -> PineconeVectorStore:
    global _vector_store
    
    # 1. Embedding Modelini Yükle
    print("[RAG] BGE-M3 embedding modeli yükleniyor...")
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # 2. Pinecone API Anahtarını ve Index Adını Al
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    index_name = "estu-index" # Pinecone panelinde oluşturduğun isim

    if not pinecone_api_key:
        raise ValueError("[RAG] HATA: .env dosyasında PINECONE_API_KEY bulunamadı!")

    # 3. Pinecone Bulut Bağlantısını Kur
    print(f"[RAG] Pinecone Bulut Veritabanına bağlanılıyor (Index: {index_name})...")
    
    _vector_store = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings,
        pinecone_api_key=pinecone_api_key
    )
    
    print("[RAG] Pinecone Bulut bağlantısı BAŞARILI.")
    return _vector_store