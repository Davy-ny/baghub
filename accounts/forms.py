from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from .models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    admin_code = forms.CharField(max_length=50, required=False, help_text="If you are an admin, enter the secret code")

    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'password1', 'password2', 'admin_code')

    def clean_admin_code(self):
        code = self.cleaned_data.get('admin_code')
        if code:
            if code == settings.ADMIN_SECRET_CODE:
                return code
            else:
                raise forms.ValidationError("Invalid admin code.")
        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        # Set role to admin if valid admin code provided
        if self.cleaned_data.get('admin_code'):
            user.role = 'admin'
        if commit:
            user.save()
        return user