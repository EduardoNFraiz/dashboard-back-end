from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label=_("Endereço de email"),
        widget=forms.TextInput(attrs={'autofocus': True})
    )

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Tenta encontrar o usuário pelo e-mail (que será o 'username' fornecido)
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        
        # Verifica se a senha está correta
        if user.check_password(password):
            return user
        return None