from .models import User


def can_manage_records(user):
    return user.is_authenticated and (
        user.is_superuser or user.role == User.Role.ADMIN
    )
