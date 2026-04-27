from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from accounts.models import User
from .models import Batch, Holiday, Task

MONTHLY_CAPACITY = Decimal(settings.TRMS_MONTHLY_CAPACITY)
AVAILABILITY_THRESHOLD = Decimal(settings.TRMS_AVAILABILITY_THRESHOLD)
ALMOST_FULL_THRESHOLD = Decimal(settings.TRMS_ALMOST_FULL_THRESHOLD)


def get_schedule(target_date):
    return (
        Task.objects.filter(date=target_date)
        .select_related("trainer")
        .order_by("trainer__name", "task_type")
    )


def get_visible_tasks(user):
    queryset = Task.objects.select_related("trainer", "trainer__trainer_profile__circle")
    if user.role == User.Role.TRAINER:
        return queryset.filter(trainer=user)
    if user.role == User.Role.CIRCLE_LEAD:
        return queryset.filter(trainer__trainer_profile__circle__manager=user)
    return queryset


def get_visible_batches(user):
    queryset = Batch.objects.select_related("trainer", "circle").prefetch_related("holidays")
    if user.role == User.Role.TRAINER:
        return queryset.filter(trainer=user)
    if user.role == User.Role.CIRCLE_LEAD:
        return queryset.filter(circle__manager=user)
    return queryset


def calculate_occupancy(trainer, year, month):
    total_hours = (
        Task.objects.filter(trainer=trainer, date__year=year, date__month=month)
        .aggregate(total=Sum("hours"))
        .get("total")
        or Decimal("0")
    )
    remaining = MONTHLY_CAPACITY - total_hours
    if remaining > AVAILABILITY_THRESHOLD:
        label, color = "Available", "success"
    elif remaining > 0 and remaining < ALMOST_FULL_THRESHOLD:
        label, color = "Almost Full", "warning"
    elif remaining <= 0:
        label, color = "Fully Occupied", "danger"
    else:
        label, color = "Balanced", "info"
    occupancy = (total_hours / MONTHLY_CAPACITY) * 100 if MONTHLY_CAPACITY else 0
    return {
        "assigned_hours": float(total_hours),
        "remaining_hours": float(remaining),
        "occupancy_percent": round(float(occupancy), 2),
        "status": label,
        "color": color,
    }


def build_calendar_events(user):
    events = []
    task_queryset = get_visible_tasks(user)
    for task in task_queryset.select_related("trainer"):
        events.append(
            {
                "title": f"{task.trainer.name}: {task.get_task_type_display()} ({task.hours}h)",
                "start": task.date.isoformat(),
                "color": "#0d6efd" if task.status == Task.Status.APPROVED else "#ffc107",
            }
        )
    for holiday in Holiday.objects.all():
        events.append({"title": f"Holiday: {holiday.description}", "start": holiday.date.isoformat(), "color": "#dc3545"})
    for batch in get_visible_batches(user):
        for item in batch.assessment_dates:
            events.append({"title": f"Assessment: {batch.name}", "start": item, "color": "#198754"})
    return events


def generate_notifications(user):
    notifications = []
    today = timezone.localdate()
    trainers = defaultdict(int)
    visible_tasks = get_visible_tasks(user)
    for task in visible_tasks.filter(date__gte=today - timedelta(days=2), date__lte=today):
        trainers[task.trainer_id] += 1
    for batch in get_visible_batches(user).filter(end_date__range=[today, today + timedelta(days=7)]):
        notifications.append(f"Batch '{batch.name}' ends on {batch.end_date}.")
    if user.role == User.Role.TRAINER:
        if not visible_tasks.filter(date__gte=today - timedelta(days=2), date__lte=today).exists():
            notifications.append("You have been free for 3 days.")
    else:
        for trainer_id, count in trainers.items():
            if count == 0:
                notifications.append(f"Trainer ID {trainer_id} has been free for 3 days.")
    for batch in get_visible_batches(user):
        seen = set()
        for assessment_date in batch.assessment_dates:
            if assessment_date in seen:
                notifications.append(f"Assessment clash in batch '{batch.name}' on {assessment_date}.")
            seen.add(assessment_date)
    return notifications
