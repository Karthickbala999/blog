from django.urls import path
from . import views


urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    # Authentication pages
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_dashboard, name='profile_dashboard'),
    path('oauth/google/', views.google_oauth_start, name='google_oauth_start'),
    path('oauth/google/callback/', views.google_oauth_callback, name='google_oauth_callback'),
    # Custom admin (not Django admin site)
    path('manage/', views.manage_dashboard, name='manage_dashboard'),
    path('manage/login/', views.manage_login, name='manage_login'),
    path('manage/logout/', views.manage_logout, name='manage_logout'),
    path('manage/posts/new/', views.manage_post_create, name='manage_post_create'),
    path('manage/posts/<int:pk>/edit/', views.manage_post_edit, name='manage_post_edit'),
    path('manage/posts/<int:pk>/delete/', views.manage_post_delete, name='manage_post_delete'),
]

