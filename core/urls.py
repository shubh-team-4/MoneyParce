from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, darkMode

urlpatterns = [
    # Public pages
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),

    # User authentication
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('darkmode/', darkMode.toggle_theme, name='dark mode'),
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='core/password_change.html',
        success_url='/'
    ), name='password_change'),

    # Admin/User management
    path('users/', views.user_list, name='user_list'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),

    # New routes for financial features
    path('transaction/new/', views.create_transaction, name='create_transaction'),
    path('category/new/', views.add_category, name='add_category'),
    path('budget/', views.set_budget, name='set_budget'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reports/', views.reports, name='reports'),
    path('reports/export/', views.export_pdf, name='export_pdf'),
    path('admin/advice/', views.review_financial_advice, name='review_financial_advice'),
]
