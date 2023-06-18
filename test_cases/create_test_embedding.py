from sentence_transformers import SentenceTransformer

# Load a pre-trained model
model = SentenceTransformer('distilbert-base-nli-mean-tokens')

# Define the input sentence
sentence = "This is an example sentence."

# Generate the vector embedding for the sentence
embedding = model.encode([sentence])

# Print the vector embedding
print(embedding)

# what's the dimension of the embedding?
print(len(embedding[0]))

# save it for uploading to pinecone. has to be a json file
# example:
# {
#   "vectors": [
#     {
#       "id": "item_0",
#       "metadata": {
#         "category": "sports",
#         "colors": [
#           "blue",
#           "red",
#           "green"
#         ],
#         "time_stamp": 0
#       },
#       "values": [
#         0.7066318686760833,
#         0.6970894090913603,
#         0.7463149328001745,
#         ...
#       ]
#     },
#     ...
#   ]


import json

# reformat to a savable json according to example

# create a list of dictionaries
# each dictionary is a vector
# each vector has an id, metadata, and values
# metadata is a dictionary
# values is a list of floats
# id is a string
# metadata is a dictionary

ret_json = []
for i, vec in enumerate(embedding):
    # if it's float32, convert to float64
    vec = vec.astype('float64')
    ret_json.append({
        "id": str(i),
        "metadata": {},
        "values": vec.tolist(),
    })

# package it
ret_json = {"vectors": ret_json}

# save it
with open('test_embedding.json', 'w') as f:
    json.dump(ret_json, f)
