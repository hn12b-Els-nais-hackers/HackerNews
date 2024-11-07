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
    if request.user.is_authenticated:
        submissions = submissions.exclude(hidden_by=request.user)
    return render(request, 'News/news.html', {'submissions': submissions})

# Pàgina de submissions més recents: mostra les submissions ordenades per data de creació
def newest(request):
    submissions = Submission.objects.all().order_by('-created_at')  # Ordena per més recent
    if request.user.is_authenticated:
        submissions = submissions.exclude(hidden_by=request.user)
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

@login_required
def upvote_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    if request.user not in submission.voters.all():
        submission.points += 1
        submission.voters.add(request.user)
        submission.save()
    next_page = request.GET.get('next', 'newest')
    return redirect(next_page)

@login_required
def unvote_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    if request.user in submission.voters.all():
        submission.points -= 1
        submission.voters.remove(request.user)
        submission.save()
    return redirect('newest')

@login_required
def hide_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    submission.hidden_by.add(request.user)
    next_page = request.GET.get('next', 'news')
    return redirect(next_page)

@login_required
def hidden_submissions(request):
    submissions = Submission.objects.filter(hidden_by=request.user).order_by('-created_at')
    return render(request, 'News/hidden_submissions.html', {'submissions': submissions})

@login_required
def unhide_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    if request.user in submission.hidden_by.all():
        submission.hidden_by.remove(request.user)
        submission.save()
    return redirect('hidden_submissions')
    