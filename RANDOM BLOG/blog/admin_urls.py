# blog/admin_urls.py
from django.urls import path
from . import admin_views

urlpatterns = [
    path('', admin_views.dashboard, name='blog_admin_dashboard'),
    path('posts/', admin_views.manage_posts, name='manage_blog_posts'),
]
