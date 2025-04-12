from .models import UserProfile

from .models import UserProfile
from django.contrib.auth.models import AnonymousUser


def theme_context(request):
    theme = 'light'

    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            theme = user_profile.theme
        except UserProfile.DoesNotExist:
            pass
    else:
        theme = request.session.get('theme', 'light')  # Default to 'light'

    return {'theme': theme}