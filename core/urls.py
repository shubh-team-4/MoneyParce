from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Public pages
    path('', views.index, name='index'),  # Info page
    path('about/', views.about, name='about'),

    # User authentication
    path('signup/', views.signup, name='signup'),  # Sign up page
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),

    # Password change (requires user to be logged in)
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='core/password_change.html',
        success_url='/'
    ), name='password_change'),

    # Admin/User management (accessible only to admin/staff)
    path('users/', views.user_list, name='user_list'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
]
