from langchain_ollama import OllamaEmbeddings
import chromadb
from openai import OpenAI

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

    candidates = [
        (doc, dist) for doc, dist in zip(documents, distances)
        if dist < DISTANCE_THRESHOLD
    ]

    query_keywords = query.lower().split()
    keyword_matches = []
    other_matches = []

    for doc, dist in candidates:
        doc_lower = doc.lower()
        if any(keyword in doc_lower for keyword in query_keywords):
            keyword_matches.append((doc, dist))
        else:
            other_matches.append((doc, dist))

    combined = keyword_matches + other_matches
    top_candidates = [doc for doc, dist in combined[:10]]
    return rerank(query, top_candidates, top_n=n_results)


def rerank(query: str, candidates: list[str], top_n: int = 3) -> list[str]:
    if not candidates:
        return []

    if len(candidates) <= top_n:
        return candidates

    numbered = "\n\n".join(
        f"[{i+1}] {doc}" for i, doc in enumerate(candidates)
    )

    prompt = f"""You are a search relevance judge. A user asked: "{query}"

Here are {len(candidates)} candidate passages from a knowledge base:

{numbered}

Return ONLY the numbers of the {top_n} most relevant passages, in order of relevance, as a comma-separated list like: 2, 1, 4

Do not explain. Just the numbers."""

    llm = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    response = llm.chat.completions.create(
        model="qwen2.5",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content.strip()

    try:
        indices = [int(x.strip()) - 1 for x in raw.split(",")]
        return [candidates[i] for i in indices if 0 <= i < len(candidates)]
    except Exception:
        return candidates[:top_n]