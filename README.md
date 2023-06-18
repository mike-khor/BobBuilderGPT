# BobBuilderGPT
For CalHacks Hackathon 2023, team members: Mike Khor, Autumn Rains, Eric Danforth, Meera Vinod


# Development

Set up your API access tokens in source, for example:

```
export OPENAI_API_KEY='sk-xxxxxxxxxxxx'
export OPENAI_ORGANIZATION='org-xxxxxxxxxxxxxx'
export PINECONE_API_KEY='xxxxx-xxxxxxx-xxxxxx'
```

install poetry

```
pip install poetry
```

install dependencies

```
poetry install
```

run main app script

```
cd chatbot_proj
poetry run python manage.py runserver
```