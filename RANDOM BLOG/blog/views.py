import secrets
from urllib.parse import urlencode

import requests
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect

from .models import Post, PostVisit

GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'


def post_list(request):
    posts = Post.objects.filter(published=True)
    return render(request, 'blog/post_list.html', {'posts': posts})


def post_detail(request, slug: str):
    post = get_object_or_404(Post, slug=slug, published=True)
    if request.user.is_authenticated:
        PostVisit.objects.create(user=request.user, post=post)
    return render(request, 'blog/post_detail.html', {'post': post})


# --- Authentication views ---

def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile_dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('profile_dashboard')
    else:
        form = AuthenticationForm()
    
    return render(request, 'auth/login.html', {'form': form})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('profile_dashboard')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile_dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'auth/signup.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('post_list')


def _ensure_google_oauth_config():
    if not settings.GOOGLE_OAUTH_CLIENT_ID or not settings.GOOGLE_OAUTH_CLIENT_SECRET:
        raise ImproperlyConfigured(
            'Google OAuth requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.'
        )


def google_oauth_start(request):
    _ensure_google_oauth_config()
    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state
    params = {
        'response_type': 'code',
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
        'scope': ' '.join(settings.GOOGLE_OAUTH_SCOPE),
        'state': state,
        'access_type': 'offline',
        'prompt': 'select_account',
    }
    return redirect(f'{GOOGLE_AUTH_URL}?{urlencode(params)}')


def google_oauth_callback(request):
    _ensure_google_oauth_config()
    expected_state = request.session.pop('google_oauth_state', None)
    state = request.GET.get('state')
    if not expected_state or state != expected_state:
        return HttpResponseBadRequest('Invalid OAuth state.')
    code = request.GET.get('code')
    if not code:
        return HttpResponseBadRequest('Authorization code missing.')
    try:
        token_response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                'code': code,
                'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
                'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
                'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
                'grant_type': 'authorization_code',
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10,
        )
        token_response.raise_for_status()
    except requests.RequestException:
        return HttpResponseBadRequest('Unable to exchange code with Google.')

    token_payload = token_response.json()
    access_token = token_payload.get('access_token')
    if not access_token:
        return HttpResponseBadRequest('Google did not return an access token.')

    try:
        userinfo_response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
        userinfo_response.raise_for_status()
    except requests.RequestException:
        return HttpResponseBadRequest('Unable to fetch Google profile information.')

    profile = userinfo_response.json()
    email = profile.get('email')
    if not email:
        return HttpResponseBadRequest('Google account does not expose an email address.')

    user = _sync_google_user(profile)
    login(request, user)
    return redirect('profile_dashboard')


def _sync_google_user(profile: dict):
    User = get_user_model()
    email = profile.get('email')
    given_name = profile.get('given_name', '')
    family_name = profile.get('family_name', '')

    user = User.objects.filter(email__iexact=email).first()
    if user:
        updated_fields = []
        if given_name and user.first_name != given_name:
            user.first_name = given_name
            updated_fields.append('first_name')
        if family_name and user.last_name != family_name:
            user.last_name = family_name
            updated_fields.append('last_name')
        if updated_fields:
            user.save(update_fields=updated_fields)
        return user

    base_username = (email.split('@')[0] or 'googleuser').lower()
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f'{base_username}{counter}'
        counter += 1

    user = User(
        username=username,
        email=email,
        first_name=given_name,
        last_name=family_name,
    )
    user.set_unusable_password()
    user.save()
    return user


@login_required
def profile_dashboard(request):
    visits = request.user.post_visits.select_related('post').all()
    total_posts = visits.values_list('post_id', flat=True).distinct().count()
    return render(
        request,
        'profile/dashboard.html',
        {
            'visits': visits,
            'total_posts': total_posts,
        },
    )


# --- Custom admin (simple) ---

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'slug', 'image', 'body', 'published']
        help_texts = {
            'slug': 'Leave blank to auto-generate from the title.',
        }
        widgets = {
            'body': forms.Textarea(attrs={'rows': 6}),
        }


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


def manage_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('manage_dashboard')
        return redirect('post_list')
    form = LoginForm(request.POST or None)
    error = None
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user is not None:
            login(request, user)
            return redirect('manage_dashboard')
        error = 'Invalid credentials'
    return render(request, 'manage/login.html', {'form': form, 'error': error})


@login_required(login_url='manage_login')
def manage_logout(request):
    logout(request)
    return redirect('manage_login')


def staff_required(view_func):
    @login_required(login_url='manage_login')
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped


@staff_required
def manage_dashboard(request):
    posts = Post.objects.all()
    return render(request, 'manage/dashboard.html', {'posts': posts})


@staff_required
def manage_post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_dashboard')
    return render(request, 'manage/post_form.html', {'form': form, 'mode': 'create'})


@staff_required
def manage_post_edit(request, pk: int):
    post = get_object_or_404(Post, pk=pk)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_dashboard')
    return render(request, 'manage/post_form.html', {'form': form, 'mode': 'edit', 'post': post})


@staff_required
def manage_post_delete(request, pk: int):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        post.delete()
        return redirect('manage_dashboard')
    return render(request, 'manage/post_confirm_delete.html', {'post': post})
