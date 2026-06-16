from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

User = get_user_model()

_INPUT_CLASS = "form-control"


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"class": _INPUT_CLASS, "placeholder": "correo@ejemplo.com", "autofocus": True}),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": _INPUT_CLASS, "placeholder": "••••••••"}),
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"class": _INPUT_CLASS, "placeholder": "correo@ejemplo.com"}),
    )
    first_name = forms.CharField(
        label="Nombre",
        max_length=150,
        widget=forms.TextInput(attrs={"class": _INPUT_CLASS}),
    )
    last_name = forms.CharField(
        label="Apellido",
        max_length=150,
        widget=forms.TextInput(attrs={"class": _INPUT_CLASS}),
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({"class": _INPUT_CLASS})
        self.fields["password2"].widget.attrs.update({"class": _INPUT_CLASS})
        self.fields["password1"].label = "Contraseña"
        self.fields["password2"].label = "Confirmar contraseña"

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Ya existe una cuenta con ese correo electrónico.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.rol = User.Rol.CLIENTE
        user.username = self._unique_username(user.email)
        if commit:
            user.save()
        return user

    @staticmethod
    def _unique_username(email):
        base = email.split("@")[0]
        username, n = base, 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{n}"
            n += 1
        return username
