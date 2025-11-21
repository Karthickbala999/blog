# blog/admin_views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from .models import BlogPost  # Replace with your actual model name
from django.contrib.auth.models import User
user = User.objects.get(username='yourusername')
user.is_staff = True
user.save()



def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)

@login_required
@staff_required
def dashboard(request):
    return render(request, 'blog/admin_dashboard.html')
    

@login_required
@staff_required
def manage_posts(request):
    posts = BlogPost.objects.all()
    return render(request, 'blog/post_list.html', {'posts': posts})