from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class JobSeekerSignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'job_seeker'
        user.username = user.email.split('@')[0]  # Auto-generate username from email
        if commit:
            user.save()
        return user


class RecruiterSignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'recruiter'
        user.username = user.email.split('@')[0]  # Auto-generate username from email
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Email Address", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}))
