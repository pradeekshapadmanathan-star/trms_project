from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("bootstrap-admin/", views.bootstrap_admin, name="bootstrap_admin"),
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.create_user, name="create_user"),
    path("users/<int:user_id>/delete/", views.delete_user, name="delete_user"),
    path("circles/", views.circle_list, name="circle_list"),
    path("circles/create/", views.create_circle, name="create_circle"),
    path("circles/<int:circle_id>/delete/", views.delete_circle, name="delete_circle"),
]
