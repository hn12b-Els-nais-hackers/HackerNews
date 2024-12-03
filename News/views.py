from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from .models import Submission, UserProfile, Comment
from .serializers import (
    SubmissionSerializer,
    UserProfileSerializer,
    CommentSerializer,
    UserSerializer,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework_api_key.authentication import APIKeyAuthentication


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing submissions.
    """
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [APIKeyAuthentication]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        submission = self.get_object()
        if request.user in submission.voters.all():
            submission.voters.remove(request.user)
            submission.points -= 1
        else:
            submission.voters.add(request.user)
            submission.points += 1
        submission.save()
        return Response({"points": submission.points}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        submission = self.get_object()
        if request.user in submission.favorited_by.all():
            submission.favorited_by.remove(request.user)
        else:
            submission.favorited_by.add(request.user)
        submission.save()
        return Response({"favorited": request.user in submission.favorited_by.all()})


class CommentViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing comments.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [APIKeyAuthentication]

    def perform_create(self, serializer):
        submission_id = self.request.data.get("submission")
        submission = get_object_or_404(Submission, id=submission_id)
        serializer.save(author=self.request.user, submission=submission)

    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        comment = self.get_object()
        if request.user in comment.voters.all():
            comment.voters.remove(request.user)
            comment.points -= 1
        else:
            comment.voters.add(request.user)
            comment.points += 1
        comment.save()
        return Response({"points": comment.points}, status=status.HTTP_200_OK)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing user profiles.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def upload_avatar(self, request, pk=None):
        profile = self.get_object()
        avatar = request.FILES.get("avatar")
        if avatar:
            profile.avatar = avatar
            profile.save()
            return Response({"avatar": profile.avatar.url}, status=status.HTTP_200_OK)
        return Response({"error": "No avatar uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def upload_banner(self, request, pk=None):
        profile = self.get_object()
        banner = request.FILES.get("banner")
        if banner:
            profile.banner = banner
            profile.save()
            return Response({"banner": profile.banner.url}, status=status.HTTP_200_OK)
        return Response({"error": "No banner uploaded"}, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    """
    Endpoint to get or update the current logged-in user's profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def post(self, request):
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FavoriteSubmissionsListView(ListAPIView):
    """
    Lists all favorite submissions of the current user.
    """
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Submission.objects.filter(favorited_by=self.request.user)


class HiddenSubmissionsListView(ListAPIView):
    """
    Lists all hidden submissions of the current user.
    """
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Submission.objects.filter(hidden_by=self.request.user)
