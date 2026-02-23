"""Route decorators for role-based access."""
from functools import wraps
from flask import abort
from flask_login import current_user


def staff_required(f):
    """Only Admin or Staff can access."""
    @wraps(f)
    def inner(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.is_staff:
            abort(403)
        return f(*args, **kwargs)
    return inner
