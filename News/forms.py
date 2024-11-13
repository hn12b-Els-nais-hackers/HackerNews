from django import forms
from .models import Submission
from django.contrib.auth.forms import UserChangeForm
from .models import UserProfile
from .models import Submission, Comment

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['title', 'url', 'text', 'submission_type']

    def clean(self):
        cleaned_data = super().clean()
        submission_type = cleaned_data.get('submission_type')
        url = cleaned_data.get('url')

        # Check if submission type is 'url' and URL is provided
        if submission_type == 'url':
            if not url:
                self.add_error('url', "URL is required for URL submissions.")
            elif Submission.objects.filter(url=url).exists():
                self.add_error('url', "This URL has already been submitted.")
                
        # Additional checks for 'ask' submissions, if needed
        text = cleaned_data.get('text')
        if submission_type == 'ask' and not text:
            self.add_error('text', "Text is required for ask submissions.")

        return cleaned_data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('avatar', 'banner', 'about')
        

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'banner', 'about']
