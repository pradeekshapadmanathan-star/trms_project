from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models

from accounts.models import Circle


class Holiday(models.Model):
    date = models.DateField(unique=True)
    description = models.CharField(max_length=255)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.date} - {self.description}"


class Batch(models.Model):
    name = models.CharField(max_length=255)
    course = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="batches",
        limit_choices_to={"role": "trainer"},
    )
    circle = models.ForeignKey(Circle, on_delete=models.SET_NULL, null=True, blank=True, related_name="batches")
    holidays = models.ManyToManyField(Holiday, blank=True, related_name="batches")
    assessment_dates = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} - {self.course}"


class Task(models.Model):
    class TaskType(models.TextChoices):
        TRAINING = "training", "Training"
        DECK = "deck", "Deck"
        PROJECT = "project", "Project"
        CONTENT = "content", "Content"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
        limit_choices_to={"role": "trainer"},
    )
    date = models.DateField()
    task_type = models.CharField(max_length=20, choices=TaskType.choices)
    hours = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(24)])
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["-date", "trainer__name"]

    def __str__(self):
        return f"{self.trainer} - {self.date} - {self.task_type}"


class FileUpload(models.Model):
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploads",
        limit_choices_to={"role": "trainer"},
    )
    file = models.FileField(
        upload_to="uploads/",
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "ppt", "pptx", "doc", "docx"])],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.trainer} - {self.file.name}"
