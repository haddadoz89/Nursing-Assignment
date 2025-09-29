# In main_app/backends.py

from django.contrib.auth.backends import ModelBackend
from .models import User
from phonenumber_field.phonenumber import to_python


class PhoneOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        phone_number = to_python(username, region="BH")

        if phone_number and phone_number.is_valid():
            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                return None
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password):
            return user
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None