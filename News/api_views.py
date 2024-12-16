from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from .models import UserProfile, Submission, Comment
from .serializers import (
    UserProfileSerializer, 
    SubmissionSerializer, 
    CommentSerializer, 
    UserProfileUpdateSerializer,
    SubmissionListSerializer,
    CommentListSerializer,
    CommentCreateSerializer
)
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
import boto3
from django.conf import settings
from django.contrib.auth.models import User
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class UserProfileAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        operation_id='get_user_profile',
        responses={
            200: UserProfileSerializer,
            404: 'User profile not found'
        },
        operation_description="Get user profile details including karma points"
    )
    def get(self, request, username):
        user_profile = get_object_or_404(UserProfile, user__username=username)
        submission_karma = sum(s.points for s in Submission.objects.filter(user=user_profile.user))
        comment_karma = sum(c.points for c in Comment.objects.filter(author=user_profile.user))
        
        serializer = UserProfileSerializer(user_profile)
        data = serializer.data
        data['karma'] = submission_karma + comment_karma
        return Response(data)

    @swagger_auto_schema(
        operation_id='update_profile_media',
        manual_parameters=[
            openapi.Parameter('avatar', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
            openapi.Parameter('banner', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
            openapi.Parameter('about', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
        ],
        responses={200: UserProfileSerializer}
    )
    def post(self, request, username):
        if request.user.username != username:
            return Response({"error": "Cannot modify other users' profiles"}, status=status.HTTP_403_FORBIDDEN)
            
        user_profile = get_object_or_404(UserProfile, user__username=username)
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
            region_name=os.getenv('AWS_S3_REGION_NAME')
        )

        for field, folder in [('avatar', 'avatars'), ('banner', 'banners')]:
            if field in request.FILES:
                file_obj = request.FILES[field]
                s3_key = f"{folder}/{file_obj.name}"
                s3.upload_fileobj(file_obj, os.getenv('AWS_STORAGE_BUCKET_NAME'), s3_key)
                setattr(user_profile, field, s3_key)

        if 'about' in request.data:
            user_profile.about = request.data['about']
        
        user_profile.save()
        return Response(UserProfileSerializer(user_profile).data)

class SubmissionAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_id='list_submissions',
        manual_parameters=[
            openapi.Parameter('type', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False, enum=['url', 'ask']),
            openapi.Parameter('order', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False, enum=['newest', 'points']),
        ],
        responses={200: SubmissionListSerializer(many=True)}
    )
    def get(self, request):
        submissions = Submission.objects.all()
        
        # Filter by type
        submission_type = request.query_params.get('type')
        if submission_type:
            submissions = submissions.filter(submission_type=submission_type)
            
        # Order submissions
        order = request.query_params.get('order', 'newest')
        if order == 'newest':
            submissions = submissions.order_by('-created_at')
        else:
            submissions = submissions.order_by('-points')
            
        # Exclude hidden submissions for authenticated users
        if request.user.is_authenticated:
            submissions = submissions.exclude(hidden_by=request.user)
            
        serializer = SubmissionListSerializer(submissions, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_id='create_submission',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['title', 'submission_type'],
            properties={
                'title': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Title of the submission'
                ),
                'url': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='URL for the submission (required if submission_type is "url")'
                ),
                'text': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Text content (required if submission_type is "ask")'
                ),
                'submission_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['url', 'ask'],
                    description='Type of submission'
                ),
            }
        ),
        responses={
            201: SubmissionSerializer,
            400: 'Invalid submission data or URL already exists'
        }
    )
    def post(self, request):
        submission_type = request.data.get('submission_type')
        url = request.data.get('url')
        
        # Check for duplicate URL if it's a URL submission
        if submission_type == 'url':
            if not url:
                return Response(
                    {"error": "URL is required for URL submissions"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Submission.objects.filter(url=url).exists():
                return Response(
                    {
                        "error": "This URL has already been submitted",
                        "url": url,
                        "duplicate": True
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif submission_type == 'ask' and not request.data.get('text'):
            return Response(
                {"error": "Text is required for Ask submissions"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = SubmissionSerializer(data=request.data)
        if serializer.is_valid():
            submission = serializer.save(user=request.user)
            submission.voters.add(request.user)  # Auto-upvote
            submission.points = 1
            submission.save()
            return Response(SubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubmissionDetailAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_id='submission_action',
        manual_parameters=[
            openapi.Parameter(
                'action',
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                enum=['vote', 'unvote', 'hide', 'unhide', 'favorite', 'unfavorite'],
                required=True,
                description='Action to perform on the submission'
            )
        ],
        responses={
            200: openapi.Response(
                description="Action performed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: 'Invalid action',
            404: 'Submission not found'
        }
    )
    def post(self, request, submission_id):
        submission = get_object_or_404(Submission, id=submission_id)
        action = request.query_params.get('action')
        
        actions = {
            'vote': (submission.voters.add, {'points': 1}),
            'unvote': (submission.voters.remove, {'points': -1}),
            'hide': (submission.hidden_by.add, {}),
            'unhide': (submission.hidden_by.remove, {}),
            'favorite': (submission.favorited_by.add, {}),
            'unfavorite': (submission.favorited_by.remove, {})
        }
        
        if action in actions:
            action_func, extra = actions[action]
            action_func(request.user)
            if 'points' in extra:
                submission.points += extra['points']
                submission.save()
            return Response({"message": f"Submission {action}d successfully"})
            
        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_id='delete_submission',
        responses={
            200: openapi.Response(
                description="Submission deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'submission_id': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            403: 'Not authorized (not the submission author)',
            404: 'Submission not found'
        }
    )
    def delete(self, request, submission_id):
        submission = get_object_or_404(Submission, id=submission_id)
        
        # Check if user is the author
        if submission.user != request.user:
            return Response({
                "error": "You can only delete your own submissions",
                "submission_id": submission_id
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Store info before deletion    
        submission_data = {
            "message": "Submission deleted successfully",
            "submission_id": submission_id,
            "title": submission.title
        }
        
        submission.delete()
        return Response(submission_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id='update_submission',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'url': openapi.Schema(type=openapi.TYPE_STRING),
                'text': openapi.Schema(type=openapi.TYPE_STRING),
                'submission_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['url', 'ask']
                ),
            }
        ),
        responses={
            200: SubmissionSerializer,
            400: 'Invalid data or URL already exists',
            403: 'Not authorized (not the submission author)',
            404: 'Submission not found'
        }
    )
    def put(self, request, submission_id):
        submission = get_object_or_404(Submission, id=submission_id)
        
        # Check if user is the author
        if submission.user != request.user:
            return Response({
                "error": "You can only edit your own submissions",
                "submission_id": submission_id
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check for duplicate URL if URL is being changed
        if 'url' in request.data and request.data['url'] != submission.url:
            if Submission.objects.filter(url=request.data['url']).exists():
                return Response({
                    "error": "This URL has already been submitted",
                    "url": request.data['url'],
                    "duplicate": True
                }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = SubmissionSerializer(submission, data=request.data, partial=True)
        if serializer.is_valid():
            submission = serializer.save()
            return Response(SubmissionSerializer(submission).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class SubmissionSearchAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_id='search_submissions',
        manual_parameters=[
            openapi.Parameter(
                'q',
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='Search query for submission titles'
            )
        ],
        responses={
            200: SubmissionListSerializer(many=True),
            404: 'No submissions found'
        },
        operation_description="Search for submissions by title"
    )
    def get(self, request):
        submissions = Submission.objects.all()
        print(f"submissions:{submissions}")
        query = request.GET.get('Title of the Submission', '')
        print(f"Search query: {query}")  # Debugging line
        if query:
            # Filter the submissions based on the query
            submissions = submissions.filter(title__icontains=query)
            print(f"Filtered submissions: {submissions}")  # Debugging line
            
            if request.user.is_authenticated:
                submissions = submissions.exclude(hidden_by=request.user)
        else:
            submissions = Submission.objects.none()
        
        serializer = SubmissionListSerializer(submissions, many=True)
        return Response(serializer.data)

class CommentAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_id='create_comment',
        request_body=CommentCreateSerializer,
        manual_parameters=[
            openapi.Parameter(
                'submission_id',
                openapi.IN_PATH,
                required=True,
                type=openapi.TYPE_INTEGER,
                description='ID of the submission you want to comment on'
            )
        ],
        responses={
            201: CommentSerializer,
            400: 'Invalid request data',
            404: 'Submission not found'
        },
        operation_description="""
        Create a new comment on a submission.

        The submission_id is passed in the URL path.
        Only provide the comment text and optionally a parent_id for replies.

        Example request body:
        {
            "text": "Your comment text here"
        }

        For replies to other comments:
        {
            "text": "Your reply text here",
            "parent_id": 123
        }
        """
    )
    def post(self, request, submission_id):
        submission = get_object_or_404(Submission, id=submission_id)
        
        serializer = CommentCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Check if parent comment exists and belongs to the same submission
            parent_id = serializer.validated_data.get('parent_id')
            if parent_id:
                try:
                    parent = Comment.objects.get(id=parent_id, submission=submission)
                except Comment.DoesNotExist:
                    return Response(
                        {"error": "Parent comment not found or does not belong to this submission"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
            comment = serializer.save(
                author=request.user,
                submission=submission
            )
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CommentDetailAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_id='comment_action',
        manual_parameters=[
            openapi.Parameter(
                'action',
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                enum=['vote', 'unvote', 'hide', 'unhide', 'favorite', 'unfavorite'],
                required=True,
                description='Action to perform on the comment'
            )
        ],
        responses={
            200: openapi.Response(
                description="Action performed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: 'Invalid action',
            404: 'Comment not found'
        }
    )
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        action = request.query_params.get('action')
        
        actions = {
            'vote': (comment.voters.add, {'points': 1}),
            'unvote': (comment.voters.remove, {'points': -1}),
            'hide': (comment.hidden_by.add, {}),
            'unhide': (comment.hidden_by.remove, {}),
            'favorite': (comment.favorited_by.add, {}),
            'unfavorite': (comment.favorited_by.remove, {})
        }
        
        if action in actions:
            action_func, extra = actions[action]
            action_func(request.user)
            if 'points' in extra:
                comment.points += extra['points']
                comment.save()
            return Response({"message": f"Comment {action}d successfully"})
            
        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_id='delete_comment',
        responses={
            200: openapi.Response(
                description="Comment deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'comment_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'submission_id': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            403: 'Not authorized (not the comment author)',
            404: 'Comment not found'
        }
    )
    def delete(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        
        # Check if user is the author
        if comment.author != request.user:
            return Response({
                "error": "You can only delete your own comments",
                "comment_id": comment_id,
                "submission_id": comment.submission.id
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Store info before deletion
        comment_data = {
            "message": "Comment deleted successfully",
            "comment_id": comment_id,
            "submission_id": comment.submission.id
        }
        
        comment.delete()
        return Response(comment_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id='update_comment',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['text'],
            properties={
                'text': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Updated comment text'
                )
            }
        ),
        responses={
            200: CommentSerializer,
            400: 'Invalid data',
            403: 'Not authorized (not the comment author)',
            404: 'Comment not found'
        }
    )
    def put(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        
        # Check if user is the author
        if comment.author != request.user:
            return Response({
                "error": "You can only edit your own comments",
                "comment_id": comment_id,
                "submission_id": comment.submission.id
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            comment = serializer.save()
            return Response(CommentSerializer(comment).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserContentAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_id='get_user_content',
        manual_parameters=[
            openapi.Parameter(
                'content_type',
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                enum=['submissions', 'comments', 'upvoted', 'hidden', 'favorites'],
                required=True
            )
        ],
        responses={
            200: SubmissionListSerializer(many=True),
            404: 'User not found'
        }
    )
    def get(self, request, username, content_type=None):
        user = get_object_or_404(User, username=username)
        content_type = content_type or request.query_params.get('content_type', 'submissions')
        response_data = {}

        if content_type == 'submissions':
            submissions = Submission.objects.filter(user=user).order_by('-created_at')
            response_data['submissions'] = SubmissionListSerializer(submissions, many=True).data

        elif content_type == 'comments':
            comments = Comment.objects.filter(author=user).order_by('-created_at')
            response_data['comments'] = CommentListSerializer(comments, many=True).data

        elif content_type == 'upvoted':
            submissions = Submission.objects.filter(voters=user).order_by('-created_at')
            comments = Comment.objects.filter(voters=user).order_by('-created_at')
            response_data['submissions'] = SubmissionListSerializer(submissions, many=True).data
            response_data['comments'] = CommentListSerializer(comments, many=True).data

        elif content_type == 'hidden':
            submissions = Submission.objects.filter(hidden_by=user).order_by('-created_at')
            comments = Comment.objects.filter(hidden_by=user).order_by('-created_at')
            response_data['submissions'] = SubmissionListSerializer(submissions, many=True).data
            response_data['comments'] = CommentListSerializer(comments, many=True).data

        elif content_type == 'favorites':
            submissions = Submission.objects.filter(favorited_by=user).order_by('-created_at')
            comments = Comment.objects.filter(favorited_by=user).order_by('-created_at')
            response_data['submissions'] = SubmissionListSerializer(submissions, many=True).data
            response_data['comments'] = CommentListSerializer(comments, many=True).data

        return Response(response_data)
