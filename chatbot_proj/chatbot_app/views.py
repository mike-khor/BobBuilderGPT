from django.shortcuts import render
from .forms import ChatForm
import subprocess
import shlex
import json

# from django.http import HttpResponse


def str_formatter_for_argparse(text: str):
    """
    This function takes in a string and formats it for argparse.
    """
    text = text.replace("'", "''")
    text = text.replace('"', '""')
    return text


def perform_full_loop(
    user_role: str,
    building_type: str,
    user_message: str,
):
    """
    This function takes in the user's role, building type, and message, and performs the full loop of the CodeQuery.
    """
    command_ptq = (
        f"python3 ../prompt_to_query/prompt_to_query.py "
        f"--user_role='{str_formatter_for_argparse(user_role)}' "
        f"--building_type='{str_formatter_for_argparse(building_type)}' "
        f"--user_message='{str_formatter_for_argparse(user_message)}'"
    )
    command_ptq = shlex.split(command_ptq)
    process = subprocess.Popen(command_ptq, stdout=subprocess.PIPE)
    output_ptq, error = process.communicate()

    print(output_ptq)

    # next, use infer_embedder.py to convert each line of the output to a vector
    formated_output_ptq = " ".join(output_ptq.decode("utf-8").split("\n"))
    formated_output_ptq = formated_output_ptq.replace("[", "").replace("]", "").replace(",", "")
    print(formated_output_ptq)

    command_embed = (
        f"python3 ../embedding/infer_embedder.py "
        f"--input_strings {formated_output_ptq} "
        f"--embedding_model_path='../embedding/models/fake_embedder_model' "

    )
    command_embed = shlex.split(command_embed)
    process = subprocess.Popen(command_embed, stdout=subprocess.PIPE)
    output_embed, error = process.communicate()

    output_embed = output_embed.decode("utf-8").split("\n")[0]
    output_embed = json.loads(output_embed)
    print(output_embed)
    print(len(output_embed))

    # the output is already queried against pinecone database. We can retrieve
    # the top 5 results from the database and summarize using the following
    # python script: queried_results_to_app_response.py
    # docstring help
    # GPT-4 assistant for building codes
    # optional arguments:
    # -h, --help            show this help message and exit
    # --user_role USER_ROLE
    #                         User role (e.g. architect, engineer, etc.)
    # --building_type BUILDING_TYPE
    #                         Building type (e.g. residential, commercial, etc.)
    # --initial_user_message INITIAL_USER_MESSAGE
    #                         Initial user message (e.g. What are the structural requirements?)
    # --pinecone_response_list PINECONE_RESPONSE_LIST
    #                         List of tuples (query, (index, section_text))

    # {'matches': [{'id': 'subletter$114355', 'score': 0.406729311, 'values': [], 'metadata': {'parent_id': 'subletter$0'}},], 'namespace': 'example_namespace'}]

    formatted_output_embed = []
    for i, embed in enumerate(output_embed):
        top_match = embed['matches'][0]
        formatted_output_embed.append((output_embed[i], (top_match['id'], top_match['metadata']['parent_id'])))

        # TODO: pick off form here

    command_summarize = (
        f"python3 ../queried_results_to_app_response/queried_results_to_app_response.py "
        f"--user_role='{str_formatter_for_argparse(user_role)}' "
        f"--building_type='{str_formatter_for_argparse(building_type)}' "
        f"--initial_user_message='{str_formatter_for_argparse(user_message)}' "
        f"--pinecone_response_list='{str_formatter_for_argparse(output_embed)}' "
    )



def chat_view(request):
    if request.method == "POST":
        form = ChatForm(request.POST)
        if form.is_valid():
            user_role = form.cleaned_data['user_role']
            building_type = form.cleaned_data['building_type']
            user_message = form.cleaned_data['user_message']

            perform_full_loop(
                user_role=user_role,
                building_type=building_type,
                user_message=user_message,
            )

        else:
            print("form is not valid")
    else:
        form = ChatForm()

    return render(request, "chat.html", {'form': form})