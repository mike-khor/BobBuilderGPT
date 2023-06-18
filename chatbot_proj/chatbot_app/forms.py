from django import forms

class ChatForm(forms.Form):

    # give me free text instead of choices
    user_role = forms.CharField(
        label="CQ: To get started, can you tell me which best describes your role in the housing industry - A building inspector, a real estate agent, homeowner, or other?  I will try my best to provide the most relevant information to you.\nYou:",
    )
    building_type = forms.CharField(
        label="CQ: Awesome! Cool, are you looking up information for commercial or residential buildings? Or something else?\nYou:",
    )
    user_message = forms.CharField(
        widget=forms.Textarea,
        label="CQ: Alright, let's do it! What would you like to learn more about?\nYou:",
    )

