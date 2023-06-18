"""Create vector embeddings for text data, save the embeddings locally, which
can then be uploaded to Pinecone.

Run from one level up (not from embedding directory, but from bobbuildergpt)

Example usage:
poetry run python embedding/create_embedding.py
"""

import json
from sentence_transformers import SentenceTransformer
import utils


DEFAULT_TEXT_DATA_PATH = "test_cases/fake_building_code_output.json"
DEFAULT_EMBEDDING_MODEL_PATH = "embedding/models/fake_embedder_model"
DEFAULT_NAMESPACE = "example_namespace"

# Load and parse the structured text data
data = []
with open(DEFAULT_TEXT_DATA_PATH, 'r') as f:
    for line in f:
        data.append(json.loads(line))

# TODO: this can be parallelized if compute speed matters

# Extract text for vectorization
texts = [item['text'] for item in data]

# Preprocess the text (optional)
preprocessed_texts = [text.lower() for text in texts]

# Use a text embedder to generate vector embeddings
model = SentenceTransformer('distilbert-base-nli-mean-tokens')
# other options: 'bert-base-nli-mean-tokens', 'roberta-base-nli-mean-tokens', 'distilbert-base-nli-stsb-mean-tokens', 'paraphrase-MiniLM-L6-v2'
embeddings = model.encode(preprocessed_texts)

# moving the above functions into utils.py

# Map IDs to vector embeddings
# format:
# {
#       "id": "node_type_node_id" <-- this is a composite key (str)
#       "metadata": {
#         "parent_id": "node_type_node_id",  <-- also a composite key (str)
#       },
#       "values": [
#         0.3129859419524348,
#         ...
#       ],
#       ...
#     }


id_to_embedding = []
for item, embedding in zip(data, embeddings):
    id_to_embedding.append(
        {
            "id": utils.tuple_to_composite_key(item['id']),  # "node_type_node_id
            "metadata": {
                "parent_id": utils.tuple_to_composite_key(item['parent_id']),  # "node_type_node_id
            },
            "values": embedding.tolist(),
        }
    )


# get some information about the embedding, then save it
print(F"Embedding dimension: {embeddings.shape[1]}")
print(f"Embedding record count: {embeddings.shape[0]}")
print(f"Embedding size: {embeddings.size}")
# save the embedder model
model.save(DEFAULT_EMBEDDING_MODEL_PATH)


# save to file
# some additional header formatting:
# {
#   "vectors": [ all our vectors go here ],
#   "namespace": "example_namespace"
# }


with open("embedding/embeddings.json", 'w') as f:
    json.dump(
        {
            "vectors": id_to_embedding,
            "namespace": DEFAULT_NAMESPACE,
        },
        f,
    )
