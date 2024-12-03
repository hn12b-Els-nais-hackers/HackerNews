from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import UserSerializer, UserProfileSerializer, SubmissionSerializer, CommentSerializer
from django.shortcuts import get_object_or_404
from .models import Submission, UserProfile, Comment
from django.contrib.auth.models import User
from .permissions import IsAPIKeyValid

class ExampleAPIView(APIView):
    permission_classes = [IsAPIKeyValid]  # Use the custom permission

    def get(self, request):
        # Access the user through `request.user`
        user = request.user
        return Response({
            'message': 'This is a response for an authenticated user.',
            'username': user.username
        })


class UserProfileAPI(APIView):
    permission_classes = [IsAuthenticated]

    # GET: Fetch the user profile details in JSON format
    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        user_profile = get_object_or_404(UserProfile, user=user)
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data)

    # PUT: Update the user profile details
    def put(self, request, username):
        user = get_object_or_404(User, username=username)
        user_profile = get_object_or_404(UserProfile, user=user)
        serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubmissionAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        submissions = Submission.objects.filter(user=user)
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data)

class CommentAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        comments = Comment.objects.filter(author=user)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
