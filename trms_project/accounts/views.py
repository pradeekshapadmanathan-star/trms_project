from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import role_required
from .forms import CircleForm, TrainerProfileForm, UserRegistrationForm
from .models import Circle, TrainerProfile, User


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def user_list(request):
    users = User.objects.order_by("role", "name")
    return render(request, "accounts/user_list.html", {"users": users})


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def create_user(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        profile_form = TrainerProfileForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.role == User.Role.TRAINER:
                TrainerProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        "skills": profile_form.cleaned_data.get("skills", "") if profile_form.is_valid() else "",
                        "circle": profile_form.cleaned_data.get("circle") if profile_form.is_valid() else None,
                    },
                )
            messages.success(request, f"{user.role.title()} created successfully.")
            return redirect("accounts:user_list")
    else:
        form = UserRegistrationForm()
        profile_form = TrainerProfileForm()
    return render(request, "accounts/user_form.html", {"form": form, "profile_form": profile_form})


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        if user == request.user:
            messages.error(request, "You cannot delete your own account from here.")
            return redirect("accounts:user_list")
        user.delete()
        messages.success(request, "User deleted.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_confirm_delete.html", {"target_user": user})


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def circle_list(request):
    circles = Circle.objects.select_related("manager").all()
    return render(request, "accounts/circle_list.html", {"circles": circles})


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def create_circle(request):
    if request.method == "POST":
        form = CircleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Circle created.")
            return redirect("accounts:circle_list")
    else:
        form = CircleForm()
    return render(request, "accounts/circle_form.html", {"form": form})


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def delete_circle(request, circle_id):
    circle = get_object_or_404(Circle, pk=circle_id)
    if request.method == "POST":
        circle.delete()
        messages.success(request, "Circle deleted.")
        return redirect("accounts:circle_list")
    return render(request, "accounts/circle_confirm_delete.html", {"circle": circle})


def bootstrap_admin(request):
    if User.objects.exists():
        return redirect("login")
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Role.ADMIN
            user.is_staff = True
            user.is_superuser = True
            user.save()
            login(request, user)
            return redirect("dashboard:home")
    else:
        form = UserRegistrationForm(initial={"role": User.Role.ADMIN})
    return render(request, "accounts/bootstrap_admin.html", {"form": form})
