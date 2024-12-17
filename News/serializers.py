from rest_framework import serializers
from .models import Submission, UserProfile, Comment
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]  # Only include basic user information


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserProfile
        fields = ["id", "user", "avatar", "banner", "about"]


class SubmissionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # For individual submission detail, include full user info
    voters = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='username', many=True, required=False)  # Assuming 'voters' is a list of users, just include their usernames.

    class Meta:
        model = Submission
        fields = ["id", "title", "url", "created_at", "points", "user", "submission_type", "voters"]


# Optional: For listing submissions, you might use a simplified submission serializer:
class SubmissionListSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Only include username (simplified representation)
    
    class Meta:
        model = Submission
        fields = ["id", "title", "url", "created_at", "points", "user"]


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    submission = serializers.PrimaryKeyRelatedField(read_only=True)  # Make submission read-only
    parent_id = serializers.IntegerField(source='parent.id', read_only=True)  # Add parent_id field

    class Meta:
        model = Comment
        fields = ["id", "text", "created_at", "points", "author", "submission", "voters", "parent_id"]  # Include parent_id
        read_only_fields = ['author', 'submission', 'points', 'voters']  # Make these fields read-only


# Optional: For listing comments, you might use a simplified comment serializer:
class CommentListSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()  # Only include username (simplified representation)
    parent_id = serializers.IntegerField(source='parent.id', read_only=True)  # Add parent_id field

    class Meta:
        model = Comment
        fields = ["id", "text", "created_at", "points", "author", "parent_id"]  # Include parent_id


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['about', 'avatar', 'banner']


# Basic serializers for list views
class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


# Add this serializer for comment creation
class CommentCreateSerializer(serializers.ModelSerializer):
    parent_id = serializers.IntegerField(required=False, allow_null=True)  # Add this field explicitly
    
    class Meta:
        model = Comment
        fields = ['text', 'parent_id']

    def create(self, validated_data):
        parent_id = validated_data.pop('parent_id', None)
        if parent_id:
            parent = Comment.objects.get(id=parent_id)
            validated_data['parent'] = parent
        return Comment.objects.create(**validated_data)
