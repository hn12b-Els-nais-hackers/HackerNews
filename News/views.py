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
    # Obtener todos los comentarios ordenados por fecha de creación
    comments = Comment.objects.select_related('author', 'submission').order_by('-created_at')
    return render(request, 'News/comments.html', {'comments': comments})

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
    comments = submission.submission_comments.all()
    
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
def create_comment(request, submission_id):
    if request.method == 'POST':
        submission = get_object_or_404(Submission, id=submission_id)
        text = request.POST.get('text')
        parent_id = request.POST.get('parent_id')

        if text:  # Solo crear si hay texto
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id)
                    comment = Comment.objects.create(
                        submission=submission,
                        text=text,
                        author=request.user,
                        parent=parent_comment
                    )
                except Comment.DoesNotExist:
                    pass
            else:
                comment = Comment.objects.create(
                    submission=submission,
                    text=text,
                    author=request.user
                )

    return redirect('submission_comments', submission_id=submission_id)

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
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Verificar que el usuario actual es el autor del comentario
    if comment.author != request.user:
        return redirect('submission_comments', submission_id=comment.submission.id)
    
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            comment.text = text
            comment.save()
    
    return redirect('submission_comments', submission_id=comment.submission.id)

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Verificar que el usuario actual es el autor del comentario
    if comment.author == request.user:
        submission_id = comment.submission.id
        comment.delete()
        return redirect('submission_comments', submission_id=submission_id)
    
    return redirect('submission_comments', submission_id=comment.submission.id)

