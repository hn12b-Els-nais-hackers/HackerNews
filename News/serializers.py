from rest_framework import serializers
from .models import Submission, UserProfile, Comment
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserProfile
        fields = ["id", "user", "avatar", "banner", "about"]


class SubmissionSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Submission
        fields = ["id", "title", "url", "created_at", "points", "user", "submission_type", "voters"]


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer()

    class Meta:
        model = Comment
        fields = ["id", "text", "created_at", "points", "author", "submission", "voters"]
