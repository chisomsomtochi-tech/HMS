from django import forms
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm, UserCreationForm

from core.forms import TailwindFormMixin

from .models import User


class StaffCreateForm(TailwindFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["username"].widget.attrs["placeholder"] = "e.g. dr.bello"
        self.fields["first_name"].widget.attrs["placeholder"] = "First name"
        self.fields["last_name"].widget.attrs["placeholder"] = "Last name"
        self.fields["email"].widget.attrs["placeholder"] = "name@clinic.example"
        self.fields["phone"].widget.attrs["placeholder"] = "+234 800 000 0000"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.must_change_password = True
        if commit:
            user.save()
        return user


class StaffEditForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True


class StaffPasswordResetForm(TailwindFormMixin, SetPasswordForm):
    def save(self, commit=True):
        user = super().save(commit=commit)
        user.must_change_password = True
        if commit:
            user.save(update_fields=["must_change_password"])
        return user


class StyledPasswordChangeForm(TailwindFormMixin, PasswordChangeForm):
    pass
