"""Given a trained model, input a list of strings, get a vectorized query, and
query it on pinecone.

Requirements:
pinecone api key: set as environment variable PINECONE_API_KEY

Example usage: (use foo bar baz)
poetry run python embedding/infer_embedder.py --input_strings "foo" "bar foo" "baz foo bar"

More relevant example:
poetry run python embedding/infer_embedder.py --input_strings "hospital sprinklers"

"""

import argparse
import copy
import json
import os
import typing

from sentence_transformers import SentenceTransformer
import pinecone

import utils

import sys
sys.path.append("../")


DEFAULT_EMBEDDING_MODEL_PATH = "embedding/models/chapter_1_embedder"
DEFAULT_EMBEDDING_PATH = "embedding/embeddings.json"
PINECONE_INDEX_NAME = "california-codes"
PINECONE_ENVIRONMENT = "asia-southeast1-gcp-free"
PINECONE_NAMESPACE = None


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


NODE_TYPES = ["root", "chapter", "article", "section", "subsection", "number", "letter", "subletter", "roman_numeral"]

def component_key_to_readable_section(
    component_id: str,  # composite key
):
    """Recursively find the parent, append all levels and titles together to
    get a readable section."""

    # derive from `data`
    id_to_embedding = []
    for d in data:
        id_to_embedding.append(
            {
                "id": utils.tuple_to_composite_key(d["id"]),
                "metadata": {
                    "title": d["title"],
                    "text": d["text"],
                    "parent_id": utils.tuple_to_composite_key(d["parent_id"]),
                },
            }
        )

    def _get_parent_id_recursive(component_id_list: typing.List[str]):
        """Recursively get the parent id."""
        # find the parent id of the component
        # id_to_embedding is a list of dicts
        for ref_comp in id_to_embedding:
            if ref_comp["id"] == component_id_list[-1]:
                # hack: only return something if it's a subsection or below; don't display the root, chapter, or article
                comp_type = utils.composite_key_to_tuple(ref_comp["id"])[0]  # this is like "level_2" etc
                comp_type_int = int(comp_type.split("_")[1])
                if comp_type_int >= 4:
                    return (
                        component_id_list
                        + _get_parent_id_recursive([ref_comp["metadata"]["parent_id"]])
                    )
                else:
                    return component_id_list

        return component_id_list

    lineage = list(reversed(_get_parent_id_recursive([component_id])))

    # get all the titles
    readable_section = []
    for component_id in lineage:
        for ref_comp in id_to_embedding:
            if ref_comp["id"] == component_id:
                if len((ref_title := ref_comp["metadata"]["title"]).split(" ")) <= 10:
                    readable_section.append(ref_title)
                break

    ret = " ".join(readable_section)

    # the first item in lineage is section (e.g. "13-412") -- 13 represents the chapter, 4 represents the article. The section is the full "13-412"
    # Let's add "Chapter 13, Article 4," to the beginning of the string
    try:
        chapter = readable_section[0].split("-")[0]
        article = readable_section[0].split("-")[1]
        # here article could be "710.", "2104."
        # what we need: "7", "21"
        article = article.split(".")[0][0:-2]
        ret = f"Chapter {chapter}, Article {article}, " + ret
    except:
        pass

    return ret



def augment_results_with_local_embeddings(
    results: typing.List[typing.Dict[str, typing.Any]],
    embedding_path: str = DEFAULT_EMBEDDING_PATH,
):
    """Results are missing crucial information like the text, title, and
    parent_id. We'll augment the results with the local embeddings file."""
    # load the embeddings from file
    with open(embedding_path, 'r') as f:
        id_to_embedding = json.load(f)["vectors"]

    # create a mapping from id to embedding
    id_to_embedding = {item["id"]: item for item in id_to_embedding}

    # augment the results with the local embeddings

    for result in results:
        for item in result["matches"]:
            original_composite_key = copy.copy(item["id"])
            readable_lineage_itself = component_key_to_readable_section(original_composite_key)
            readable_lineage_parent = component_key_to_readable_section(id_to_embedding[original_composite_key]["metadata"]["parent_id"])
            item["id"] = readable_lineage_itself
            item["metadata"] = {
                "text": id_to_embedding[original_composite_key]["metadata"]["text"],
                "title": id_to_embedding[original_composite_key]["metadata"]["title"],
                "parent_id": readable_lineage_parent,
            }

    return results


# argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Vectorize a list of strings.')
    parser.add_argument('--input_strings', nargs='+', help='List of strings to vectorize.')
    parser.add_argument('--embedding_model_path', default=DEFAULT_EMBEDDING_MODEL_PATH, help='Path to embedding model.')
    parser.add_argument('--embedding_path', default=DEFAULT_EMBEDDING_PATH, help='Path to embedding json file.')
    parser.add_argument('--local_building_code_data_path', default="process_pdf_to_jsonl/building_code_output.jsonl", help='Path to local data jsonl file.')
    parser.add_argument('--pinecone_index_name', default=PINECONE_INDEX_NAME, help='Name of pinecone index to query.')
    parser.add_argument('--pinecone_environment', default=PINECONE_ENVIRONMENT, help='Name of pinecone environment to query.')
    parser.add_argument('--pinecone_namespace', default=PINECONE_NAMESPACE, help='Name of pinecone namespace to query.')
    parser.add_argument('--top_k', default=10, help='Number of results to return.')

    args = parser.parse_args()

    with open(args.local_building_code_data_path, 'r') as f:
        data = []
        for line in f:
            d = json.loads(line)
            data.append(d)

    # HACK: combine input strings into just one string
    combined_input_string = " ".join(args.input_strings)
    vectorized_queries = vectorize_queries([combined_input_string], args.embedding_model_path)
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

    augmented_results = augment_results_with_local_embeddings(results_serializable, args.embedding_path)

    print(json.dumps(augmented_results))
