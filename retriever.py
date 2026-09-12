from langchain_ollama import OllamaEmbeddings
import chromadb

embeddings = OllamaEmbeddings(model="nomic-embed-text")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("knowledge_base")

DISTANCE_THRESHOLD = 0.7

def retrieve(query: str, n_results: int = 3) -> list[str]:
    query_embedding = embeddings.embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "distances"]
    )

    documents = results["documents"][0]
    distances = results["distances"][0]

    filtered = [
        doc for doc, dist in zip(documents, distances)
        if dist < DISTANCE_THRESHOLD
    ]

    return filtered