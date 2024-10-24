from django.shortcuts import render, redirect
from .models import Submission, Comment
from .forms import SubmissionForm, CommentForm
from django.utils import timezone
from django.contrib.auth.models import User

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
            #form.save()
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

