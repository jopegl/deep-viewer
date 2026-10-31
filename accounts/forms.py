from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def clean_email(self):
        email = self.cleaned_data["email"]
        existe = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if existe.exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email.lower()

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")

