from langchain_ollama import OllamaEmbeddings
import chromadb

query = "what are your shipping costs?"

embeddings = OllamaEmbeddings(model="nomic-embed-text")
query_embedding = embeddings.embed_query(query)

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("knowledge_base")

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3
)

for i, doc in enumerate(results["documents"][0]):
    print(f"\n--- Result {i+1} ---")
    print(doc)