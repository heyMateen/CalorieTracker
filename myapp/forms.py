from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Enter a valid email address.')
    phone_number = forms.CharField(max_length=15, required=False, help_text='Optional. Enter your phone number.')

    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'password1', 'password2')