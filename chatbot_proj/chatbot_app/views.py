from django.shortcuts import render
from .forms import ChatForm
import subprocess
import shlex

# from django.http import HttpResponse


def str_formatter_for_argparse(text: str):
    """
    This function takes in a string and formats it for argparse.
    """
    text = text.replace("'", "''")
    text = text.replace('"', '""')
    return text


def chat_view(request):
    if request.method == "POST":
        form = ChatForm(request.POST)
        if form.is_valid():
            user_role = form.cleaned_data['user_role']
            building_type = form.cleaned_data['building_type']
            user_message = form.cleaned_data['user_message']

            command = (
                f"python3 ../prompt_to_query/prompt_to_query.py "
                f"--user_role='{str_formatter_for_argparse(user_role)}' "
                f"--building_type='{str_formatter_for_argparse(building_type)}' "
                f"--user_message='{str_formatter_for_argparse(user_message)}'"
            )
            command = shlex.split(command)
            process = subprocess.Popen(command, stdout=subprocess.PIPE)
            output, error = process.communicate()
            # More logic here...
            # do a simple print
            print(output)

        else:
            print("form is not valid")
    else:
        form = ChatForm()

    return render(request, "chat.html", {'form': form})