from django.shortcuts import render, redirect, get_object_or_404
from .models import Submission, UserProfile, Comment
from .forms import SubmissionForm, CommentForm
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import ProfileImageForm
from django.shortcuts import HttpResponse
from django.conf import settings
import boto3
from django.contrib import messages
from django.db import models

@login_required
def test_s3_upload(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        aws_session_token=getattr(settings, 'AWS_SESSION_TOKEN', None),
        region_name=settings.AWS_S3_REGION_NAME,
    )

    # Update about field if it's part of the POST data
    if request.method == 'POST' and 'about' in request.POST:
        about_text = request.POST['about']
        user_profile.about = about_text  # Update the about field
        user_profile.save()

    if request.method == 'POST' and 'avatar' in request.FILES:
        avatar_file = request.FILES['avatar']
        s3_key = f"avatars/{avatar_file.name}"

        try:
            # Upload avatar to S3
            s3.upload_fileobj(avatar_file, settings.AWS_STORAGE_BUCKET_NAME, s3_key)

            # Update UserProfile with the new avatar URL
            user_profile.avatar = s3_key
            user_profile.save()

        except Exception as e:
            return HttpResponse(f"Error uploading avatar: {e}")

    if request.method == 'POST' and 'banner' in request.FILES:
        banner_file = request.FILES['banner']
        s3_key = f"banners/{banner_file.name}"

        try:
            # Upload banner to S3
            s3.upload_fileobj(banner_file, settings.AWS_STORAGE_BUCKET_NAME, s3_key)

            # Update UserProfile with the new banner URL
            user_profile.banner = s3_key
            user_profile.save()

        except Exception as e:
            return HttpResponse(f"Error uploading banner: {e}")

    # Redirect back to the profile page after the upload
    return redirect('profile', username=request.user.username)

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

# Pàgina principal: mostra les submissions ordenades per punts
def news(request):
    # Excluir submissions de tipo 'ask'
    submissions = Submission.objects.filter(submission_type='url').order_by('-points')
    if request.user.is_authenticated:
        submissions = submissions.exclude(hidden_by=request.user)
    return render(request, 'News/news.html', {'submissions': submissions})

# Pàgina de submissions més recents: mostra les submissions ordenades per data de creació
def newest(request):
    # Excluir submissions de tipo 'ask'
    submissions = Submission.objects.filter(submission_type='url').order_by('-created_at')
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
            submission.created_at = timezone.now()
            submission.points = 0
            submission.user = request.user
            submission.save()

            # Redirect based on submission type
            if submission.submission_type == 'ask':
                return redirect('ask')
            else:
                return redirect('newest')
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
    if request.user != submission.user:
        messages.error(request, "You can't edit this submission because you're not the author.")
        next_page = request.GET.get('next', 'newest')
        return redirect(next_page)

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
@login_required
def delete_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Verificar si el usuario actual es el autor de la submission
    if request.user != submission.user:
        messages.error(request, "You can't delete this submission because you're not the author.")
        next_page = request.GET.get('next', 'newest')
        return redirect(next_page)
        
    if request.method == 'POST':
        submission.delete()
        messages.success(request, 'Submission deleted successfully.')
        next_page = request.GET.get('next', 'newest')
        return redirect(next_page)

    return render(request, 'News/delete_submission.html', {'submission': submission})

# Pàgina de cerca: mostra les submissions que contenen el títol cercat
def search(request):
    query = request.GET.get('q', '')
    if query:
        # Buscar solo en el título
        submissions = Submission.objects.filter(
            title__icontains=query
        ).order_by('-created_at')
        
        # Si el usuario está autenticado, excluir las submissions ocultas
        if request.user.is_authenticated:
            submissions = submissions.exclude(hidden_by=request.user)
    else:
        submissions = Submission.objects.none()
    
    return render(request, 'News/search_results.html', {
        'submissions': submissions, 
        'query': query
    })

def ask(request):
    # Solo mostrar submissions de tipo 'ask'
    ask_submissions = Submission.objects.filter(submission_type='ask').order_by('-created_at')
    if request.user.is_authenticated:
        ask_submissions = ask_submissions.exclude(hidden_by=request.user)
    return render(request, 'News/ask.html', {'submissions': ask_submissions})

def comments(request):
    comments = Comment.objects.all().order_by('-created_at')
    return render(request, 'News/comments.html', {'comments': comments})

def login(request):
    return render(request, 'News/login.html')

@login_required
def threads(request):
    comments = Comment.objects.filter(author=request.user).order_by('-created_at')
    
    # Crear una lista de comentarios con información de next/prev
    comments_list = list(comments)
    for i, comment in enumerate(comments_list):
        if i > 0:
            comment.previous_comment = comments_list[i-1]
        if i < len(comments_list) - 1:
            comment.next_comment = comments_list[i+1]
    
    return render(request, 'News/threads.html', {'comments': comments_list})

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
    context_comment_id = request.GET.get('context')
    
    # Si hay un context_comment_id, obtener el comentario y sus ancestros
    context_comment = None
    context_tree = []
    if context_comment_id:
        try:
            context_comment = Comment.objects.get(id=context_comment_id)
            current = context_comment
            while current.parent:
                context_tree.append(current.parent)
                current = current.parent
        except Comment.DoesNotExist:
            pass
    
    # Manejar el voto (mantener el código existente)
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
        'context_comment': context_comment,
        'context_tree': context_tree,
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
    user = get_object_or_404(User, username=username)
    user_profile = get_object_or_404(UserProfile, user=user)

    submission_karma = Submission.objects.filter(user=user).aggregate(total_points=models.Sum('points'))['total_points'] or 0
    comment_karma = Comment.objects.filter(author=user).aggregate(total_points=models.Sum('points'))['total_points'] or 0
    total_karma = submission_karma + comment_karma

    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            # Saving the form will automatically handle S3 upload based on 'upload_to' path
            form.save()
            return redirect('profile', username=user.username)
        else:
            print("Form errors:", form.errors)
    else:
        form = ProfileImageForm(instance=user_profile)

    return render(request, 'News/profile.html', {'form': form, 'user_profile': user_profile, 'user': user, 'karma': total_karma})

# Pàgina de submissions de l'usuari: mostra les submissions de l'usuari
def user_submissions(request, username):
    user = get_object_or_404(User, username=username)
    submissions = Submission.objects.filter(user=user).order_by('-created_at')  # Ordenades per data de creació, més recents primer
    return render(request, 'News/user_submissions.html', {'user': user, 'submissions': submissions})


# Pàgina de comentaris de l'usuari: mostra els comentaris de l'usuari
def user_comments(request, username):
    user = get_object_or_404(User, username=username)
    comments = Comment.objects.filter(author=user).order_by('-created_at')
    return render(request, 'News/user_comments.html', {'user': user, 'comments': comments})

# Pàgina de submissions votades de l'usuari: mostra les submissions votades de l'usuari
def user_upvoted(request, username):
    viewed_user = get_object_or_404(User, username=username)
    
    # Get all upvoted submissions and comments using the voters field
    upvoted_submissions = Submission.objects.filter(voters=viewed_user).order_by('-created_at')
    upvoted_comments = Comment.objects.filter(voters=viewed_user).order_by('-created_at')
    
    return render(request, 'News/user_upvoted.html', {
        'viewed_user': viewed_user,
        'upvoted_submissions': upvoted_submissions,
        'upvoted_comments': upvoted_comments,
    })

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