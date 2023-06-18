from django import forms

class ChatForm(forms.Form):
    CQ_RESPONSE_CHOICES = (
        ('inspector', 'Inspector'),
        ('re_agent', 'Real Estate Agent'),
        ('homeowner', 'Homeowner'),
        ('other', 'Other')
    )
    BT_RESPONSE_CHOICES = (
        ('commercial', 'Commercial'),
        ('residential', 'Residential'),
        ('other', 'Other')
    )
    # user_role = forms.ChoiceField(choices=CQ_RESPONSE_CHOICES, label="To get started, can you tell me which best describes your role in the housing industry - A building inspector, a real estate agent, homeowner, or other?  I will try my best to provide the most relevant information to you.")
    # building_type = forms.ChoiceField(choices=BT_RESPONSE_CHOICES, label="Awesome! Cool, are you looking up information for commercial or residential buildings? Or something else?")
    # user_message = forms.CharField(widget=forms.Textarea, label="Awesome, let's do it then! What would you like to learn more about?")

    # give me free text instead of choices
    user_role = forms.CharField(label="To get started, can you tell me which best describes your role in the housing industry - A building inspector, a real estate agent, homeowner, or other?  I will try my best to provide the most relevant information to you.")
    building_type = forms.CharField(label="Awesome! Cool, are you looking up information for commercial or residential buildings? Or something else?")
    user_message = forms.CharField(widget=forms.Textarea, label="Awesome, let's do it then! What would you like to learn more about?")

