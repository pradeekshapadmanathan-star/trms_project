from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Circle, TrainerProfile, User


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "name", "email", "role", "password1", "password2"]


class TrainerProfileForm(forms.ModelForm):
    class Meta:
        model = TrainerProfile
        fields = ["skills", "circle"]
        widgets = {"skills": forms.Textarea(attrs={"rows": 3})}


class CircleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manager"].queryset = User.objects.filter(
            role__in=[User.Role.MANAGER, User.Role.CIRCLE_LEAD]
        ).order_by("name")

    class Meta:
        model = Circle
        fields = ["name", "manager"]
