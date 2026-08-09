from datetime import date

from django import forms
from django.contrib.auth import get_user_model

from .models import Profile


User = get_user_model()

MINIMUM_AGE = 13
MINIMUM_BIRTH_YEAR = 1900


def get_maximum_birth_date():
    today = date.today()

    try:
        return today.replace(
            year=today.year - MINIMUM_AGE
        )
    except ValueError:
        return today.replace(
            year=today.year - MINIMUM_AGE,
            day=28,
        )


class LoginForm(forms.Form):
    username = forms.CharField()

    password = forms.CharField(
        widget=forms.PasswordInput
    )


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
    )

    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "email",
        ]

    def clean_password2(self):
        password = self.cleaned_data.get(
            "password"
        )

        password2 = self.cleaned_data.get(
            "password2"
        )

        if password and password2 != password:
            raise forms.ValidationError(
                "Passwords do not match."
            )

        return password2

    def clean_email(self):
        email = self.cleaned_data["email"]

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "Email already exists."
            )

        return email


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
        ]

    def clean_email(self):
        email = self.cleaned_data["email"]

        if (
            User.objects
            .exclude(pk=self.instance.pk)
            .filter(email__iexact=email)
            .exists()
        ):
            raise forms.ValidationError(
                "Email already exists."
            )

        return email


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "date_of_birth",
            "photo",
        ]

        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date",
                    "min": (
                        f"{MINIMUM_BIRTH_YEAR}"
                        "-01-01"
                    ),
                },
                format="%Y-%m-%d",
            ),
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.fields[
            "date_of_birth"
        ].widget.attrs["max"] = (
            get_maximum_birth_date()
            .isoformat()
        )

    def clean_date_of_birth(self):
        date_of_birth = (
            self.cleaned_data.get(
                "date_of_birth"
            )
        )

        if not date_of_birth:
            return date_of_birth

        if (
            date_of_birth
            > get_maximum_birth_date()
        ):
            raise forms.ValidationError(
                "You must be at least "
                f"{MINIMUM_AGE} years old."
            )

        if (
            date_of_birth.year
            < MINIMUM_BIRTH_YEAR
        ):
            raise forms.ValidationError(
                "Please enter a valid "
                "date of birth."
            )

        return date_of_birth