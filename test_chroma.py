import chromadb

client = chromadb.Client()
collection = client.create_collection("test")
collection.add(documents=["hello world"], ids=["1"])
print("Chroma works:", collection.count())