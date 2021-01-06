from app.models.user import User
from django.contrib.auth.hashers import (check_password,)
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission
from django.db.models import Q

class TokenBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):

        try:
            user = User.objects.get(Q(username=username)|Q(email=username))
        except User.DoesNotExist:
            return None

        if user.check_password(password):
                return user

