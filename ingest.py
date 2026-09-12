from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
import chromadb

# Load knowledge base
with open("knowledge_base.txt", "r") as f:
    text = f.read()

# Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
chunks = splitter.split_text(text)

# Set up embeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Set up persistent Chroma
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("knowledge_base")

# Add chunks
for i, chunk in enumerate(chunks):
    embedding = embeddings.embed_query(chunk)
    collection.add(
        documents=[chunk],
        embeddings=[embedding],
        ids=[f"chunk_{i}"]
    )

print(f"Done — {len(chunks)} chunks stored in Chroma")