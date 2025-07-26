"""
Custom authentication backends for the attendance system
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to login with email address
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user with email and password
        """
        if username is None or password is None:
            return None

        UserModel = get_user_model()

        try:
            # Try to find user by email first, then username
            user = UserModel.objects.get(
                Q(email=username) | Q(username=username)
            )

            # Check password
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            UserModel().set_password(password)
            return None

        return None

    def get_user(self, user_id):
        """
        Get user by ID
        """
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(pk=user_id)
            return user if self.user_can_authenticate(user) else None
        except UserModel.DoesNotExist:
            return None