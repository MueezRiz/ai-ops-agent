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
        n_results=10,
        include=["documents", "distances"]
    )

    documents = results["documents"][0]
    distances = results["distances"][0]

    # Filter by distance threshold
    candidates = [
        (doc, dist) for doc, dist in zip(documents, distances)
        if dist < DISTANCE_THRESHOLD
    ]

    # Keyword boost: move exact keyword matches to the front
    query_keywords = query.lower().split()
    keyword_matches = []
    other_matches = []

    for doc, dist in candidates:
        doc_lower = doc.lower()
        if any(keyword in doc_lower for keyword in query_keywords):
            keyword_matches.append((doc, dist))
        else:
            other_matches.append((doc, dist))

    # Combine: keyword matches first, then semantic-only matches
    combined = keyword_matches + other_matches

    return [doc for doc, dist in combined[:n_results]]