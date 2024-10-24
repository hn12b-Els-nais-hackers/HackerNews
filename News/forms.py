from django import forms
from .models import Submission
from django.contrib.auth.forms import UserChangeForm
from .models import UserProfile

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['title', 'url', 'text', 'submission_type']  # Correct field names

    # Ensure the URL is unique
    def clean_url(self):
        url = self.cleaned_data.get('url')
        submission_type = self.cleaned_data.get('submission_type')

        # Only validate uniqueness if the submission type is 'url'
        if submission_type == 'url' and url:
            if Submission.objects.filter(url=url).exists():
                raise forms.ValidationError("This URL has already been submitted.")
        return url

    # Validate the form fields based on the submission type
    def clean(self):
        cleaned_data = super().clean()
        submission_type = cleaned_data.get('submission_type')
        url = cleaned_data.get('url')
        text = cleaned_data.get('text')

        # URL is mandatory for 'url' submissions
        if submission_type == 'url' and not url:
            self.add_error('url', "URL is required for URL submissions.")

        # Text is mandatory for 'ask' submissions
        if submission_type == 'ask' and not text:
            self.add_error('text', "Text is required for ask submissions.")

        return cleaned_data

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('avatar', 'banner', 'about')