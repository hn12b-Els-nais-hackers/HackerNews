from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

class Submission(models.Model):
    SUBMISSION_TYPES = (
        ('url', 'URL'),
        ('ask', 'Ask'),
    )

    title = models.CharField(max_length=255)
    url = models.URLField(max_length=500, blank=True, null=True)  # Optional for ask submissions
    text = models.TextField(blank=True, null=True)  # Only used for ask submissions
    points = models.IntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    submission_type = models.CharField(max_length=10, choices=SUBMISSION_TYPES, default='url')
    created_at = models.DateTimeField(auto_now_add=True)
    voters = models.ManyToManyField(User, related_name='voted_submissions', blank=True)
    hidden_by = models.ManyToManyField(User, related_name='hidden_submissions', blank=True)
    comments = models.ManyToManyField('Comment', related_name='submissions', blank=True)
    favorited_by = models.ManyToManyField(User, related_name='favorited_submissions', blank=True)
    

    def __str__(self):
        return self.title

    def upvote(self):
        self.points += 1
        self.save()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', max_length=255, default='avatars/default_avatar.png')
    banner = models.ImageField(upload_to='banners/', max_length=255, default='banners/default_banner.jpg')
    about = models.TextField(blank=True, null=True)

    # Solución a los conflictos con las relaciones
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='user_profiles',  # Cambiamos el related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='user_profiles',  # Cambiamos el related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
class Comment(models.Model):
    text = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    submission = models.ForeignKey('Submission', related_name='submission_comments', on_delete=models.CASCADE)
    favorited_by = models.ManyToManyField(User, related_name='favorited_comments', blank=True)
    hidden_by = models.ManyToManyField(User, related_name='hidden_comments', blank=True)
    voters = models.ManyToManyField(User, related_name='voted_comments', blank=True)
    points = models.IntegerField(default=0)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    def __str__(self):
        return self.text

    def upvote(self):
        self.points += 1
        self.save()
