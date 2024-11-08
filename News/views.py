from django.shortcuts import render, redirect, get_object_or_404
from .models import Submission, UserProfile
from .forms import SubmissionForm
from django.shortcuts import render, redirect
from .models import Submission, Comment
from .forms import SubmissionForm, CommentForm
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm 

# Pàgina principal: mostra les submissions ordenades per punts
def news(request):
    submissions = Submission.objects.all().order_by('-points')  # Ordena per punts
    return render(request, 'News/news.html', {'submissions': submissions})

# Pàgina de submissions més recents: mostra les submissions ordenades per data de creació
def newest(request):
    submissions = Submission.objects.all().order_by('-created_at')  # Ordena per més recent
    return render(request, 'News/newest.html', {'submissions': submissions})

# Pàgina de submit: permet a l'usuari crear una nova submission
def submit(request):
    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.created_at = timezone.now()  # Assigna la data actual
            submission.points = 0  # Inicialment 0 punts
            #submission.author = request.user  # Suposant que tens l'usuari loguejat
            submission.user = User.objects.get(username='default_user')
            submission.save()
            form.save()
            return redirect('newest')  # Redirigeix a la pàgina newest després de crear la submission
    else:
        form = SubmissionForm()
    return render(request, 'News/submit.html', {'form': form})

def ask(request):
    return render(request, 'News/ask.html')

def comments(request):
    return render(request, 'News/comments.html')

def login(request):
    return render(request, 'News/login.html')

def threads(request):
    return render(request, 'News/threads.html')

def add_comment(request):
    form = CommentForm(request.POST)
    if form.is_valid():
        form.save()
    return redirect('News/comments.html')

def all_comments(request):
    comments = Comment.objects.all()
    return render(request, 'News/comments.html', {'comments': comments})

def submission_comments(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    comments = submission.comments.all()
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.submission = submission
            comment.save()
            return redirect('submission_comments', submission_id=submission.id)
    else:
        form = CommentForm()
    
    return render(request, 'news/submission_comments.html', {'submission': submission, 'comments': comments, 'form': form})


@login_required
def profile_view(request, username):
    # Fetch the User instance using the provided username
    user = get_object_or_404(User, username=username)
    
    # Now fetch the UserProfile using the User instance
    user_profile = get_object_or_404(UserProfile, user_id=user.id)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=user.username)  # Redirect to the profile page after saving
    else:
        form = ProfileForm(instance=user_profile)

    return render(request, 'News/profile.html', {'form': form, 'user_profile': user_profile, 'user': user})

