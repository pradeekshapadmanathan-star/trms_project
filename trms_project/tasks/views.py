import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from accounts.decorators import role_required
from accounts.models import User
from .forms import BatchForm, FileUploadForm, HolidayForm, TaskForm
from .models import Batch, FileUpload, Holiday, Task
from .services import build_calendar_events


@login_required
def task_list(request):
    queryset = Task.objects.select_related("trainer")
    if request.user.role == "trainer":
        queryset = queryset.filter(trainer=request.user)
    tasks = queryset.order_by("-date")
    return render(request, "tasks/task_list.html", {"tasks": tasks})


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def create_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Task entry saved.")
            return redirect("tasks:task_list")
    else:
        form = TaskForm()
    return render(request, "tasks/task_form.html", {"form": form})


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if request.method == "POST":
        task.delete()
        messages.success(request, "Task deleted.")
        return redirect("tasks:task_list")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})


@login_required
@role_required(User.Role.TRAINER)
def upload_file(request):
    if request.method == "POST":
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.trainer = request.user
            upload.save()
            messages.success(request, "File uploaded successfully.")
            return redirect("tasks:file_list")
    else:
        form = FileUploadForm()
    return render(request, "tasks/file_form.html", {"form": form})


@login_required
def file_list(request):
    uploads = FileUpload.objects.filter(trainer=request.user) if request.user.role == "trainer" else FileUpload.objects.all()
    return render(
        request,
        "tasks/file_list.html",
        {"uploads": uploads, "form": FileUploadForm(), "can_upload_files": request.user.role == "trainer"},
    )


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def batch_list(request):
    batches = Batch.objects.select_related("trainer", "circle").prefetch_related("holidays")
    return render(request, "tasks/batch_list.html", {"batches": batches})


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def create_batch(request):
    if request.method == "POST":
        form = BatchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Batch created.")
            return redirect("tasks:batch_list")
    else:
        form = BatchForm()
    return render(request, "tasks/batch_form.html", {"form": form})


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def delete_batch(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    if request.method == "POST":
        batch.delete()
        messages.success(request, "Batch deleted.")
        return redirect("tasks:batch_list")
    return render(request, "tasks/batch_confirm_delete.html", {"batch": batch})


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def holiday_list(request):
    holidays = Holiday.objects.all()
    return render(request, "tasks/holiday_list.html", {"holidays": holidays})


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def create_holiday(request):
    if request.method == "POST":
        form = HolidayForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Holiday added.")
            return redirect("tasks:holiday_list")
    else:
        form = HolidayForm()
    return render(request, "tasks/holiday_form.html", {"form": form})


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def delete_holiday(request, holiday_id):
    holiday = get_object_or_404(Holiday, pk=holiday_id)
    if request.method == "POST":
        holiday.delete()
        messages.success(request, "Holiday deleted.")
        return redirect("tasks:holiday_list")
    return render(request, "tasks/holiday_confirm_delete.html", {"holiday": holiday})


@login_required
def calendar_feed(request):
    return render(
        request,
        "tasks/calendar.html",
        {
            "calendar_events_json": json.dumps(build_calendar_events(request.user)),
            "manager_schedule_enabled": request.user.role == "manager",
        },
    )


@login_required
def get_schedule_by_date(request, date):
    if request.user.role != "manager":
        return HttpResponseForbidden("Managers only.")

    target_date = parse_date(date)
    if not target_date:
        return JsonResponse({"detail": "Invalid date format."}, status=400)

    schedules = (
        Task.objects.filter(date=target_date)
        .select_related("trainer")
        .order_by("trainer__name", "task_type")
    )
    payload = [
        {
            "trainer": task.trainer.name,
            "task": task.get_task_type_display(),
            "hours": float(task.hours),
            "status": task.get_status_display(),
        }
        for task in schedules
    ]
    return JsonResponse(payload, safe=False)
