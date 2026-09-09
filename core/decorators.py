from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """Restricts a view to users whose UserProfile.role is in allowed_roles.

    Must be stacked under @login_required so request.user is guaranteed authenticated.
    """

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            profile = getattr(request.user, "userprofile", None)
            if profile is None or profile.role not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
