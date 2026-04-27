from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .forms import UserRegistrationForm
from .models import Circle, TrainerProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = UserRegistrationForm
    fieldsets = DjangoUserAdmin.fieldsets + ((None, {"fields": ("name", "role")}),)
    list_display = ("username", "name", "email", "role", "is_staff")


@admin.register(TrainerProfile)
class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "circle")
    search_fields = ("user__name", "user__email")


@admin.register(Circle)
class CircleAdmin(admin.ModelAdmin):
    list_display = ("name", "manager")
