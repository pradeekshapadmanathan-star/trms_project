import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from accounts.models import Circle, User
from reports.services import generate_monthly_report
from tasks.models import Batch, Task
from tasks.services import (
    AVAILABILITY_THRESHOLD,
    build_calendar_events,
    calculate_occupancy,
    generate_notifications,
    get_schedule,
    get_visible_batches,
    get_visible_tasks,
)


@login_required
def home(request):
    role = request.user.role
    month = datetime.today().date().replace(day=1)
    today = datetime.today().date()
    base_context = {
        "notifications": generate_notifications(request.user),
        "calendar_events_json": json.dumps(build_calendar_events(request.user)),
    }
    if role == User.Role.TRAINER:
        occupancy = calculate_occupancy(request.user, month.year, month.month)
        context = {
            **base_context,
            "tasks": get_visible_tasks(request.user)[:10],
            "uploads": request.user.uploads.all()[:5],
            "occupancy": occupancy,
        }
        return render(request, "dashboard/trainer_dashboard.html", context)
    if role == User.Role.MANAGER:
        date_str = request.GET.get("date") or datetime.today().strftime("%Y-%m-%d")
        schedule = get_schedule(date_str)
        trainers = User.objects.filter(role=User.Role.TRAINER)
        occupancy_cards = [calculate_occupancy(trainer, month.year, month.month) | {"trainer": trainer} for trainer in trainers]
        task_distribution = list(Task.objects.values("task_type").annotate(total=Count("id")).order_by("task_type"))
        context = {
            **base_context,
            "selected_date": date_str,
            "schedule": schedule,
            "occupancy_cards": occupancy_cards,
            "trainer_count": trainers.count(),
            "active_batch_count": Batch.objects.filter(start_date__lte=today, end_date__gte=today).count(),
            "free_trainer_count": sum(1 for card in occupancy_cards if card["remaining_hours"] > float(AVAILABILITY_THRESHOLD)),
            "task_distribution": task_distribution,
            "report_rows": generate_monthly_report(month).to_dict(orient="records")[:5],
        }
        return render(request, "dashboard/manager_dashboard.html", context)
    if role == User.Role.CIRCLE_LEAD:
        scoped_circles = request.user.managed_circles.all()
        scoped_batches = get_visible_batches(request.user)
        scoped_tasks = get_visible_tasks(request.user)
        context = {
            **base_context,
            "circle_count": scoped_circles.count(),
            "batch_count": scoped_batches.count(),
            "trainer_count": User.objects.filter(
                role=User.Role.TRAINER,
                trainer_profile__circle__manager=request.user,
            ).distinct().count(),
            "task_status": scoped_tasks.values("status").annotate(total=Count("id")),
            "recent_batches": scoped_batches[:5],
        }
        return render(request, "dashboard/circle_lead_dashboard.html", context)
    context = {
        **base_context,
        "trainer_count": User.objects.filter(role=User.Role.TRAINER).count(),
        "manager_count": User.objects.filter(role=User.Role.MANAGER).count(),
        "batch_count": Batch.objects.count(),
        "task_count": Task.objects.count(),
        "active_batch_count": Batch.objects.filter(start_date__lte=today, end_date__gte=today).count(),
        "free_trainer_count": sum(
            1
            for trainer in User.objects.filter(role=User.Role.TRAINER)
            if calculate_occupancy(trainer, month.year, month.month)["remaining_hours"] > float(AVAILABILITY_THRESHOLD)
        ),
        "task_distribution": list(Task.objects.values("task_type").annotate(total=Count("id")).order_by("task_type")),
        "workload_rows": [
            {
                "trainer": trainer.name,
                "assigned_hours": calculate_occupancy(trainer, month.year, month.month)["assigned_hours"],
            }
            for trainer in User.objects.filter(role=User.Role.TRAINER)
        ],
        "recent_batches": Batch.objects.select_related("trainer")[:5],
    }
    return render(request, "dashboard/admin_dashboard.html", context)
