from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate
from .models import CustomUser, UserProfile, Address

class CustomAuthenticationForm(AuthenticationForm):
    login_field = forms.CharField(label="Email ou Nom d'utilisateur", max_length=254)
    secret_code = forms.CharField(label="Code secret (pour gestionnaires)", max_length=10, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'] = self.fields.pop('login_field')

    def clean(self):
        login_field = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if login_field and password:
            self.user_cache = authenticate(self.request, username=login_field, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Nom d'utilisateur/email ou mot de passe incorrect.")
            elif not self.user_cache.is_active:
                raise forms.ValidationError("Ce compte est inactif.")
        return self.cleaned_data

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        print(f"Avant save - password: {user.password}")  # Débogage
        if commit:
            user.save()
            print(f"Après save - password: {user.password}")  # Débogage
        return user

class ManagerCreationForm(CustomUserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'bio']

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['street', 'city', 'postal_code', 'country', 'is_default']