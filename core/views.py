from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden
from .forms import SignUpForm

def index(request):
    """Public page explaining MoneyParce."""
    return render(request, 'core/index.html')

def about(request):
    """Additional info about MoneyParce purpose."""
    return render(request, 'core/about.html')

def signup(request):
    """User signup view for new account creation."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # automatically log the user in
            messages.success(request, "Account created successfully!")
            return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})

# Decorator to ensure only admins can access the page
def admin_required(view_func):
    decorated_view_func = login_required(user_passes_test(lambda u: u.is_staff, login_url='/', redirect_field_name=None)(view_func))
    return decorated_view_func

@admin_required
def user_list(request):
    """Admin view to list and manage users."""
    users = User.objects.all()
    return render(request, 'core/user_list.html', {'users': users})

@admin_required
def delete_user(request, user_id):
    """Admin view to delete a user account."""
    user = get_object_or_404(User, id=user_id)
    # Prevent admin from deleting self
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('user_list')
    user.delete()
    messages.success(request, f"User '{user.username}' has been deleted.")
    return redirect('user_list')

