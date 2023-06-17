"""Run an API call to openai GPT-4"""
import argparse
import sys
import requests
import os
import json

import openai

# Set up OpenAI API credentials
openai.organization = os.getenv("OPENAI_ORGANIZATION")
openai.api_key = os.getenv("OPENAI_API_KEY")

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
REQUEST_HEADER = {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + os.getenv("OPENAI_API_KEY"),
}

# Define the GPT-4 prompt

class PromptQueryMachine:
    def __init__(
        self, user_role, building_type, messages_history: list = []
    ):
        self.messages_history = messages_history
        self.user_role = user_role
        self.building_type = building_type
        self.system_message = """output: a list of strings (["topic 1", ...]) that can form a vectorized query, separated by topics if distinct topics exist (no more than 3)"""
        self.all_responses = []

        self.add_system_message_to_history()

    def add_message_to_history(self, message):
        self.messages_history.append({"role": "user", "content": message})
        return self.messages_history

    def add_system_message_to_history(self):
        self.messages_history.append({"role": "system", "content": self.system_message})
        return self.messages_history

    def add_assistant_message_to_history(self, message):
        self.messages_history.append({"role": "assistant", "content": message})
        return self.messages_history

    def add_user_message_to_history(self, message):
        # reformat first -- add user role and building type
        fmtd_message = {"user_role": self.user_role, "building_type": self.building_type, "main_prompt": message}
        self.messages_history.append({"role": "user", "content": str(fmtd_message)})
        return self.messages_history

    def make_request(self):
        request_body = {
            "model": "gpt-4-0613",
            "messages": self.messages_history,
        }
        response = requests.post(OPENAI_URL, headers=REQUEST_HEADER, json=request_body)
        self.all_responses.append(response.json())

        # parse the response, add to history
        self.add_assistant_message_to_history(response.json()["choices"][0]["message"]["content"])

        return response.json()


if __name__ == "__main__":

    # get args
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--user_role",
        type=str,
        help="user role",
        default="homeowner",
    )
    parser.add_argument(
        "--building_type",
        type=str,
        help="building type",
        default="residential",
    )
    parser.add_argument(
        "--messages_history",
        type=list,
        help="messages history",
        default=[],
    )
    parser.add_argument(
        "--user_message",
        type=str,
        help="user message",
        default="",
    )

    args = parser.parse_args()

    pm = PromptQueryMachine(
        user_role=args.user_role,
        building_type=args.building_type,
        messages_history=args.messages_history,
    )
    pm.add_user_message_to_history(args.user_message)
    response = pm.make_request()

    # give response back as stdout
    print(response["choices"][0]["message"]["content"])

    sys.exit(0)
