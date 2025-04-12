from .models import UserProfile




def toggle_theme(request):
    # Check if user is authenticated
    if request.user.is_authenticated:
        # Logged-in user: save preference in UserProfile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.theme = 'dark' if profile.theme == 'light' else 'light'
        profile.save()
        current_theme = profile.theme
    else:
        # Anonymous user: save preference in session or cookie
        current_theme = request.session.get('theme', 'light')  # Default to 'light'
        current_theme = 'dark' if current_theme == 'light' else 'light'
        request.session['theme'] = current_theme
    from django.shortcuts import redirect
    return redirect(request.META.get('HTTP_REFERER', '/'))