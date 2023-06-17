import os
import pinecone

pinecone.init(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment="asia-southeast1-gcp-free",
)

print(pinecone.list_indexes())
