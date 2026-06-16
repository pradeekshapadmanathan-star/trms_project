from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from accounts.models import User
from .models import Batch, Holiday, ScheduleSlot, Task

MONTHLY_CAPACITY = Decimal(settings.TRMS_MONTHLY_CAPACITY)
AVAILABILITY_THRESHOLD = Decimal(settings.TRMS_AVAILABILITY_THRESHOLD)
ALMOST_FULL_THRESHOLD = Decimal(settings.TRMS_ALMOST_FULL_THRESHOLD)
def get_hours_color(hours):
    value = float(hours)
    if value <= 1:
        return "#facc15"  # yellow
    if 2 <= value <= 5:
        return "#22c55e"  # green
    if 5 < value <= 9:
        return "#3b82f6"  # blue
    if 9 < value <= 15:
        return "#a855f7"  # purple
    return "#64748b"  # fallback


BATCH_COLORS = {
    "ds": "#16a34a",
    "ai": "#2563eb",
    "ml": "#7c3aed",
    "python": "#f97316",
}

TASK_TYPE_COLORS = {
    "training": "#16a34a",
    "assessment": "#2563eb",
    "free": "#9ca3af",
    "deck": "#7c3aed",
    "project": "#f97316",
    "leave": "#facc15",
    "holiday": "#dc2626",
    "meeting": "#92400e",
    "content": "#0ea5e9",
}


def get_batch_color(name):
    lower = (name or "").lower()
    for key, color in BATCH_COLORS.items():
        if key in lower:
            return color
    return "#0ea5e9"


def get_task_type_color(task_type):
    return TASK_TYPE_COLORS.get(task_type, "#2563eb")


def get_occupancy_status(occupied_hours):
    if occupied_hours >= 9:
        return "Fully Occupied"
    if occupied_hours >= 5:
        return "Almost Full"
    return "Available"


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
        hours_color = get_hours_color(task.hours)
        events.append(
            {
                "title": f"{task.trainer.name}: {task.get_task_type_display()} ({task.hours}h)",
                "start": task.date.isoformat(),
                "color": hours_color,
                "textColor": "#0f172a" if hours_color == "#facc15" else "#ffffff",
            }
        )
    for holiday in Holiday.objects.all():
        events.append({"title": f"Holiday: {holiday.description}", "start": holiday.date.isoformat(), "color": "#dc3545"})
    for batch in get_visible_batches(user):
        current_day = batch.start_date
        while current_day <= batch.end_date:
            events.append(
                {
                    "title": f"Batch: {batch.name} ({batch.course})",
                    "start": current_day.isoformat(),
                    "color": "#20c997",
                    "textColor": "#0f172a",
                    "allDay": True,
                    "display": "block",
                }
            )
            current_day += timedelta(days=1)
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


def _visible_slots(user):
    slots = ScheduleSlot.objects.select_related("trainer", "batch", "trainer__trainer_profile__circle")
    if user.role == User.Role.TRAINER:
        return slots.filter(trainer=user)
    if user.role == User.Role.CIRCLE_LEAD:
        return slots.filter(trainer__trainer_profile__circle__manager=user)
    return slots


def get_scheduler_events(user, start_date=None, end_date=None, batch_id=None, trainer_id=None):
    slots = _visible_slots(user)
    if start_date and end_date:
        slots = slots.filter(date__range=[start_date, end_date])
    if batch_id:
        slots = slots.filter(batch_id=batch_id)
    if trainer_id:
        slots = slots.filter(trainer_id=trainer_id)

    events = []
    visible_batches = get_visible_batches(user)
    if batch_id:
        visible_batches = visible_batches.filter(pk=batch_id)
    if trainer_id:
        visible_batches = visible_batches.filter(trainer_id=trainer_id)

    # Always paint batch bands on the scheduler so batch visibility is explicit.
    for batch in visible_batches:
        band_start = max(batch.start_date, start_date) if start_date else batch.start_date
        band_end = min(batch.end_date, end_date) if end_date else batch.end_date
        if band_start > band_end:
            continue
        current = band_start
        while current <= band_end:
            start_dt = datetime.combine(current, time(8, 0))
            end_dt = datetime.combine(current, time(20, 0))
            events.append(
                {
                    "title": f"Batch: {batch.name}",
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "display": "background",
                    "backgroundColor": get_batch_color(batch.name),
                    "extendedProps": {
                        "trainer": batch.trainer.name if batch.trainer else "-",
                        "batch": batch.name,
                        "task_type": "Batch Window",
                        "start_time": "08:00 AM",
                        "end_time": "08:00 PM",
                        "duration": 12,
                        "occupancy_status": "Planned",
                        "occupancy_percent": 0,
                        "circle": batch.circle.name if batch.circle else "-",
                        "description": f"{batch.course} batch timeline",
                        "batch_color": get_batch_color(batch.name),
                        "task_color": get_batch_color(batch.name),
                    },
                }
            )
            current += timedelta(days=1)

    if slots.exists():
        for slot in slots:
            start_dt = datetime.combine(slot.date, slot.start_time)
            end_dt = datetime.combine(slot.date, slot.end_time)
            duration = round((end_dt - start_dt).total_seconds() / 3600, 2)
            batch_name = slot.batch.name if slot.batch else "N/A"
            circle_name = getattr(getattr(slot.trainer, "trainer_profile", None), "circle", None)
            circle_text = circle_name.name if circle_name else "-"
            task_color = get_task_type_color(slot.task_type)
            batch_color = get_batch_color(batch_name)
            events.append(
                {
                    "title": f"{slot.trainer.name} | {batch_name} | {slot.get_task_type_display()}",
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "backgroundColor": task_color,
                    "borderColor": batch_color,
                    "extendedProps": {
                        "trainer": slot.trainer.name,
                        "batch": batch_name,
                        "task_type": slot.get_task_type_display(),
                        "task_type_key": slot.task_type,
                        "start_time": slot.start_time.strftime("%I:%M %p"),
                        "end_time": slot.end_time.strftime("%I:%M %p"),
                        "duration": duration,
                        "occupancy_status": slot.get_occupancy_status_display(),
                        "occupancy_percent": min(round((duration / 8) * 100, 2), 100),
                        "circle": circle_text,
                        "description": f"{slot.get_task_type_display()} session",
                        "batch_color": batch_color,
                        "task_color": task_color,
                    },
                }
            )
        return events

    # Fallback for legacy Task entries when ScheduleSlot data is not populated yet.
    tasks = get_visible_tasks(user).select_related("trainer")
    if start_date and end_date:
        tasks = tasks.filter(date__range=[start_date, end_date])
    if trainer_id:
        tasks = tasks.filter(trainer_id=trainer_id)
    if batch_id:
        tasks = tasks.filter(trainer__batches__id=batch_id).distinct()

    day_tracker = defaultdict(lambda: time(9, 0))
    for task in tasks.order_by("date", "trainer_id"):
        start_time = day_tracker[(task.trainer_id, task.date)]
        total_minutes = int(float(task.hours) * 60)
        start_dt = datetime.combine(task.date, start_time)
        end_dt = start_dt + timedelta(minutes=total_minutes)
        day_tracker[(task.trainer_id, task.date)] = end_dt.time()
        batch = task.trainer.batches.filter(start_date__lte=task.date, end_date__gte=task.date).first()
        batch_name = batch.name if batch else "N/A"
        circle_name = getattr(getattr(task.trainer, "trainer_profile", None), "circle", None)
        circle_text = circle_name.name if circle_name else "-"
        task_color = get_task_type_color(task.task_type)
        batch_color = get_batch_color(batch_name)
        events.append(
            {
                "title": f"{task.trainer.name} | {batch_name} | {task.get_task_type_display()}",
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "backgroundColor": task_color,
                "borderColor": batch_color,
                "extendedProps": {
                    "trainer": task.trainer.name,
                    "batch": batch_name,
                    "task_type": task.get_task_type_display(),
                    "task_type_key": task.task_type,
                    "start_time": start_dt.strftime("%I:%M %p"),
                    "end_time": end_dt.strftime("%I:%M %p"),
                    "duration": float(task.hours),
                    "occupancy_status": get_occupancy_status(float(task.hours)),
                    "occupancy_percent": min(round((float(task.hours) / 8) * 100, 2), 100),
                    "circle": circle_text,
                    "description": task.description or "-",
                    "batch_color": batch_color,
                    "task_color": task_color,
                },
            }
        )
    return events
