"""Create vector embeddings for text data, save the embeddings locally, which
can then be uploaded to Pinecone.

Run from one level up (not from embedding directory, but from bobbuildergpt)

Example usage:
poetry run python embedding/create_embedding.py
"""

import json
from sentence_transformers import SentenceTransformer
import utils
import os
import argparse

import pinecone


DEFAULT_TEXT_DATA_PATH = "process_pdf_to_jsonl/building_code_output.jsonl"
DEFAULT_EMBEDDING_MODEL_PATH = "embedding/models/chapter_1_embedder"
DEFAULT_NAMESPACE = "california_chapter_1"
# DEFAULT_MODEL_TYPE = "paraphrase-MiniLM-L6-v2"
DEFAULT_MODEL_TYPE = "roberta-base-nli-mean-tokens"
DEFAULT_PINECONE_ENVIRONMENT = "asia-southeast1-gcp-free"

# Load and parse the structured text data
data = []
with open(DEFAULT_TEXT_DATA_PATH, 'r') as f:
    for line in f:
        d = json.loads(line)
        # if d is not informative, skip it
        if (
            (len(d['title'].split(" ")) < 5 and len(d['text'].split(" ")) < 10)
        ):
            continue
        data.append(d)

# Extract title and text for vectorization
titles = [item['title'] for item in data]
texts = [item['text'] for item in data]

# Preprocess the text (optional)  TODO: what should our preprocessing be?
preprocessed_titles = [title.lower() for title in titles]
preprocessed_texts = [text.lower() for text in texts]
combined_preprocessed_strs = [
    preprocessed_title + " " + preprocessed_text
    for preprocessed_title, preprocessed_text in zip(preprocessed_titles, preprocessed_texts)
]

if __name__ == "__main__":
    # argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bypass_encoding",
        action="store_true",
        help="Bypass encoding and just load the embeddings from a file.",
    )

    args = parser.parse_args()

    if not args.bypass_encoding:
        # Use a text embedder to generate vector embeddings
        model = SentenceTransformer(DEFAULT_MODEL_TYPE)
        # other options:
        # 'bert-base-nli-mean-tokens'
        # 'roberta-base-nli-mean-tokens'
        # 'distilbert-base-nli-mean-tokens'
        # 'distilbert-base-nli-stsb-mean-tokens'
        # 'paraphrase-MiniLM-L6-v2'
        embeddings = model.encode(combined_preprocessed_strs)

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
                        "title": item['title'],
                        "text": item['text'],  # too large, we'll just refer it later using the old fashion way
                    },
                    "values": embedding.tolist(),
                }
            )


        # get some information about the embedding, then save it
        print(f"Embedding dimension: {embeddings.shape[1]}")
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

    else:
        # load the embeddings from file
        with open("embedding/embeddings.json", 'r') as f:
            id_to_embedding = json.load(f)["vectors"]

        # load the embedder model
        model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL_PATH)


    # also, use pinecone API to upload the embedding

    # loop through the embeddings, delete all metadata
    for item in id_to_embedding:
        del item["metadata"]

    # create a pinecone client
    pinecone.init(api_key=os.environ["PINECONE_API_KEY"], environment=DEFAULT_PINECONE_ENVIRONMENT)

    # use existing index
    index = pinecone.Index(index_name="california-codes")

    # upload the embedding
    # note that there's a limit of 1000 records per call
    batch_size = 50
    index.upsert(
        vectors=id_to_embedding,
        batch_size=batch_size,
    )
