from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        TRAINER = "trainer", "Trainer"
        CIRCLE_LEAD = "circle_lead", "Circle Lead"

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TRAINER)
    circle = models.ForeignKey("Circle", on_delete=models.SET_NULL, null=True, blank=True, related_name="members")
    skills = models.TextField(blank=True)
    occupancy_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    REQUIRED_FIELDS = ["email", "name", "role"]

    def __str__(self):
        return self.name or self.username


class Circle(models.Model):
    name = models.CharField(max_length=150, unique=True)
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_circles",
        limit_choices_to={"role": User.Role.MANAGER},
    )
    lead = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_circles",
        limit_choices_to={"role": User.Role.CIRCLE_LEAD},
    )

    def __str__(self):
        return self.name


class TrainerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="trainer_profile")
    skills = models.TextField(blank=True)
    circle = models.ForeignKey(Circle, on_delete=models.SET_NULL, null=True, blank=True, related_name="trainers")

    def __str__(self):
        return f"{self.user.name} Profile"
