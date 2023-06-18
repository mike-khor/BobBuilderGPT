"""Given a trained model, input a list of strings, get a vectorized query, and
query it on pinecone.

Requirements:
pinecone api key: set as environment variable PINECONE_API_KEY

Example usage: (use foo bar baz)
poetry run python embedding/infer_embedder.py --input_strings "foo" "bar foo" "baz foo bar"
"""

import argparse
import json
import os
import typing

from sentence_transformers import SentenceTransformer
import pinecone

import utils


DEFAULT_EMBEDDING_MODEL_PATH = "embedding/models/fake_embedder_model"
PINECONE_INDEX_NAME = "fake-foo-bar-starter"
PINECONE_ENVIRONMENT = "asia-southeast1-gcp-free"
PINECONE_NAMESPACE = "example_namespace"


# Convert list of strings to vectorized queries
def vectorize_queries(
    input_strings: typing.List[str],
    embedding_model_path: str = DEFAULT_EMBEDDING_MODEL_PATH,
):
    # Load the embedding model
    model = SentenceTransformer(embedding_model_path)

    preprocessed_texts = [text.lower() for text in input_strings]
    embeddings = model.encode(preprocessed_texts)
    return embeddings.tolist()

def query_pinecone(
    vectorized_queries: typing.List[typing.List[float]],
    environment: str = PINECONE_ENVIRONMENT,
    index_name: str = PINECONE_INDEX_NAME,
    namespace: str = PINECONE_NAMESPACE,
    top_k: int = 5,
):
    # Query pinecone
    pinecone.init(api_key=os.environ["PINECONE_API_KEY"], environment=environment)
    index = pinecone.Index(index_name=index_name)
    results = []
    for vectorized_query in vectorized_queries:
        results.append(
            index.query(
                vector=vectorized_query,
                top_k=top_k,
                namespace=namespace,
                include_metadata=True,
            )
        )
    return results


# argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Vectorize a list of strings.')
    parser.add_argument('--input_strings', nargs='+', help='List of strings to vectorize.')
    parser.add_argument('--embedding_model_path', default=DEFAULT_EMBEDDING_MODEL_PATH, help='Path to embedding model.')
    parser.add_argument('--pinecone_index_name', default=PINECONE_INDEX_NAME, help='Name of pinecone index to query.')
    parser.add_argument('--pinecone_environment', default=PINECONE_ENVIRONMENT, help='Name of pinecone environment to query.')
    parser.add_argument('--pinecone_namespace', default=PINECONE_NAMESPACE, help='Name of pinecone namespace to query.')
    parser.add_argument('--top_k', default=5, help='Number of results to return.')

    args = parser.parse_args()
    vectorized_queries = vectorize_queries(args.input_strings, args.embedding_model_path)
    results = query_pinecone(
        vectorized_queries=vectorized_queries,
        environment=args.pinecone_environment,
        index_name=args.pinecone_index_name,
        namespace=args.pinecone_namespace,
        top_k=args.top_k,
    )
    # output in stdout is serialized json

    results_serializable = []
    for result in results:
        results_serializable.append(result.to_dict())

    print(json.dumps(results_serializable))
