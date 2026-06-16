from django.conf import settings
from django.core.exceptions import ValidationError
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
    task = models.ForeignKey("TaskAssignment", on_delete=models.SET_NULL, null=True, blank=True, related_name="files")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_task_files",
    )
    file = models.FileField(
        upload_to="uploads/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf", "ppt", "pptx", "doc", "docx", "xls", "xlsx", "csv", "zip"]
            )
        ],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    version = models.PositiveIntegerField(default=1)
    is_approved = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.trainer} - {self.file.name}"


class ScheduleSlot(models.Model):
    class TaskType(models.TextChoices):
        TRAINING = "training", "Training"
        ASSESSMENT = "assessment", "Assessment"
        FREE = "free", "Free Slot"
        HOLIDAY = "holiday", "Holiday"
        LEAVE = "leave", "Leave"
        DECK = "deck", "Deck Preparation"
        PROJECT = "project", "Project Support"
        MEETING = "meeting", "Meeting"

    class OccupancyStatus(models.TextChoices):
        FULLY_OCCUPIED = "full", "Fully Occupied"
        ALMOST_FULL = "almost", "Almost Full"
        AVAILABLE = "available", "Available"

    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="schedule_slots")
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name="schedule_slots")
    task_type = models.CharField(max_length=20, choices=TaskType.choices)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status_color = models.CharField(max_length=20, default="#6c757d")
    occupancy_status = models.CharField(
        max_length=20, choices=OccupancyStatus.choices, default=OccupancyStatus.AVAILABLE
    )

    class Meta:
        ordering = ["-date", "start_time"]

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")
        overlaps = (
            ScheduleSlot.objects.filter(trainer=self.trainer, date=self.date)
            .exclude(pk=self.pk)
            .filter(start_time__lt=self.end_time, end_time__gt=self.start_time)
        )
        if overlaps.exists():
            raise ValidationError("Schedule overlap detected for the selected trainer and time block.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class TaskAssignment(models.Model):
    class Priority(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class TaskType(models.TextChoices):
        TRAINING = "training", "Training"
        DECK = "deck", "Deck Preparation"
        PROJECT = "project", "Project Support"
        CONTENT = "content", "Content Development"
        ASSESSMENT = "assessment", "Assessment"
        MEETING = "meeting", "Meeting"

    task_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_task_assignments"
    )
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_assignments")
    task_type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.TRAINING)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class DailyTracker(models.Model):
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_trackers")
    date = models.DateField()
    task_type = models.CharField(max_length=20, choices=Task.TaskType.choices)
    hours = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(24)])
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Task.Status.choices, default=Task.Status.PENDING)

    class Meta:
        ordering = ["-date"]
