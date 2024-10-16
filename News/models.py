from django.db import models
from django.contrib.auth.models import User

class Submission(models.Model):
    SUBMISSION_TYPES = (
        ('url', 'URL'),
        ('ask', 'Ask'),
    )

    title = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    points = models.IntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    submission_type = models.CharField(max_length=10, choices=SUBMISSION_TYPES, default='url')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title