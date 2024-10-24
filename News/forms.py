from django import forms
from .models import Submission, Comment

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['title', 'url']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']