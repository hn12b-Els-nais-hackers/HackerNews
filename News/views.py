from django.shortcuts import render, redirect, get_object_or_404
from .models import Submission, UserProfile, Comment
from .forms import SubmissionForm, CommentForm
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm 

# Pàgina principal: mostra les submissions ordenades per punts
def news(request):
    submissions = Submission.objects.all().order_by('-points')  # Ordena per punts
    if request.user.is_authenticated:
        submissions = submissions.exclude(hidden_by=request.user).order_by('-points')
    return render(request, 'News/news.html', {'submissions': submissions})

# Pàgina de submissions més recents: mostra les submissions ordenades per data de creació
def newest(request):
    submissions = Submission.objects.all().order_by('-created_at')  # Ordena per més recent
    if request.user.is_authenticated:
        submissions = submissions.exclude(hidden_by=request.user)
    return render(request, 'News/newest.html', {'submissions': submissions})

# Pàgina de submit: permet a l'usuari crear una nova submission
@login_required  
def submit(request):
    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.created_at = timezone.now()  # Assigna la data actual
            submission.points = 0  # Inicialment 0 punts
            #submission.author = request.user  # Suposant que tens l'usuari loguejat
            submission.user = request.user
            submission.save()
            form.save()
            return redirect('newest')  # Redirigeix a la pàgina newest després de crear la submission
    else:
        form = SubmissionForm()
    return render(request, 'News/submit.html', {'form': form})

# Pàgina d'edició: permet a l'usuari editar una submission existent
def edit_submission(request, submission_id):
    # Obté la submission o torna un 404 si no existeix
    submission = get_object_or_404(Submission, id=submission_id)

    # IMPLEMENTACIÓ AMB L'USUARI LOGUEJAT
    # Comprova que l'usuari sigui el creador de la submission
    # if submission.user != request.user:
    #    return redirect('newest', submission_id=submission.id)  # Redirigeix a la pàgina de detall si no és el propietari

    if request.method == 'POST':
        form = SubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            # No cal assignar camps addicionals, només guardem els canvis
            submission = form.save(commit=False)
            submission.updated_at = timezone.now()  # Registra la data d'actualització, si necessites aquest camp
            submission.save()
            return redirect('newest')  # Redirigeix a la pàgina de detall després de l'edició
    else:
        form = SubmissionForm(instance=submission)  # Carrega el formulari amb les dades existents

    return render(request, 'News/edit_submission.html', {'form': form, 'submission': submission})

# Pagina de confirmació per eliminar una submission
def delete_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    if request.method == 'POST':
        submission.delete()
        return redirect('newest')  # Redirigeix a la vista "newest" després d'eliminar

    return render(request, 'News/delete_submission.html', {'submission': submission})

# Pàgina de perfil de l'usuari: mostra les submissions i comentaris de l'usuari
def user_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = UserProfile.objects.get(user=user)
    posts = Submission.objects.filter(user=user).order_by('-created_at')
    comments = Comment.objects.filter(author=user).order_by('-created_at')
    
    context = {
        'profile_user': user,
        'profile': profile,
        'posts': posts,
        'comments': comments,
    }
    
    return render(request, 'News/user_profile.html', context)

# Pàgina de cerca: mostra les submissions que contenen el títol cercat
def search(request):
    query = request.GET.get('q', '')
    if query:
        submissions = Submission.objects.filter(title__icontains=query)
    else:
        submissions = Submission.objects.none()  # Si no hi ha consulta, retorna un queryset buit
    return render(request, 'News/search_results.html', {'submissions': submissions, 'query': query})

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

@login_required
def submission_comments(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    comments = submission.submission_comments.exclude(hidden_by=request.user) 
    
    # Manejar el voto
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'vote':
            if request.user in submission.voters.all():
                submission.points -= 1
                submission.voters.remove(request.user)
            else:
                submission.points += 1
                submission.voters.add(request.user)
            submission.save()
        elif action == 'fav':
            if request.user in submission.favorited_by.all():
                submission.favorited_by.remove(request.user)
            else:
                submission.favorited_by.add(request.user)
            submission.save()
        elif action == 'hide':
            submission.hidden_by.add(request.user)
            submission.save()
        elif action == 'unhide':
            submission.hidden_by.remove(request.user)
            submission.save()

    return render(request, 'News/submission_comments.html', {
        'submission': submission,
        'comments': comments,
    })

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
    next_page = request.GET.get('next', 'newest')
    return redirect(next_page)

@login_required
def hide_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    submission.hidden_by.add(request.user)
    next_page = request.GET.get('next', 'news')
    return redirect(next_page)

@login_required
def hidden_submissions(request):
    submissions = Submission.objects.filter(hidden_by=request.user).order_by('-created_at')
    comments = Comment.objects.filter(hidden_by=request.user).order_by('-created_at') 
    return render(request, 'News/hidden_submissions.html', {'submissions': submissions, 'comments': comments})

@login_required
def unhide_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    if request.user in submission.hidden_by.all():
        submission.hidden_by.remove(request.user)
        submission.save()
    next_page = request.GET.get('next', request.META.get('HTTP_REFERER', 'newest'))
    return redirect(next_page)

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

@login_required
def fav_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    if request.user in submission.favorited_by.all():
        submission.favorited_by.remove(request.user)
    else:
        submission.favorited_by.add(request.user)
    submission.save()
    return redirect('submission_comments', submission_id=submission.id)

def favorite_submissions(request):
    submissions = Submission.objects.filter(favorited_by=request.user).order_by('-created_at')
    comments = Comment.objects.filter(favorited_by=request.user).order_by('-created_at')
    return render(request, 'News/favorite_submissions.html', {'submissions': submissions, 'comments': comments})

@login_required
def vote_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user in comment.voters.all():
        comment.points -= 1
        comment.voters.remove(request.user)
    else:
        comment.points += 1
        comment.voters.add(request.user)
    comment.save()
    return redirect('submission_comments', submission_id=comment.submission.id)

@login_required
def fav_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user in comment.favorited_by.all():
        comment.favorited_by.remove(request.user)
    else:
        comment.favorited_by.add(request.user)
    comment.save()
    return redirect('submission_comments', submission_id=comment.submission.id)

@login_required
def hide_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.hidden_by.add(request.user)
    return redirect('submission_comments', submission_id=comment.submission.id)

@login_required
def unhide_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.hidden_by.remove(request.user)
    comment.save()
    return redirect('submission_comments', submission_id=comment.submission.id)

