from django.shortcuts import get_object_or_404, render, redirect
from .models import Submission
from .forms import SubmissionForm
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

# Pàgina d'edició: permet a l'usuari editar una submission existent
def edit_submission(request, submission_id):
    # Obté la submission o torna un 404 si no existeix
    submission = get_object_or_404(Submission, id=submission_id)

    # Comprova que l'usuari sigui el creador de la submission
    if submission.user != request.user:
        return redirect('submission_detail', submission_id=submission.id)  # Redirigeix a la pàgina de detall si no és el propietari

    if request.method == 'POST':
        form = SubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            # No cal assignar camps addicionals, només guardem els canvis
            submission = form.save(commit=False)
            submission.updated_at = timezone.now()  # Registra la data d'actualització, si necessites aquest camp
            submission.save()
            return redirect('submission_detail', submission_id=submission.id)  # Redirigeix a la pàgina de detall després de l'edició
    else:
        form = SubmissionForm(instance=submission)  # Carrega el formulari amb les dades existents

    return render(request, 'News/edit_submission.html', {'form': form, 'submission': submission})

def ask(request):
    return render(request, 'News/ask.html')

def comments(request):
    return render(request, 'News/comments.html')

def login(request):
    return render(request, 'News/login.html')

def threads(request):
    return render(request, 'News/threads.html')


