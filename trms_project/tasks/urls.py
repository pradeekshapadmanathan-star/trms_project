from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views
from .api import ScheduleSlotViewSet, TaskAssignmentViewSet

app_name = "tasks"

router = DefaultRouter()
router.register("api/task-assignments", TaskAssignmentViewSet, basename="api-task-assignments")
router.register("api/schedule-slots", ScheduleSlotViewSet, basename="api-schedule-slots")

urlpatterns = [
    path("", views.task_list, name="task_list"),
    path("create/", views.create_task, name="create_task"),
    path("<int:task_id>/delete/", views.delete_task, name="delete_task"),
    path("schedule/<str:date>/", views.get_schedule_by_date, name="schedule_by_date"),
    path("uploads/", views.file_list, name="file_list"),
    path("uploads/add/", views.upload_file, name="upload_file"),
    path("batches/", views.batch_list, name="batch_list"),
    path("batches/create/", views.create_batch, name="create_batch"),
    path("batches/<int:batch_id>/delete/", views.delete_batch, name="delete_batch"),
    path("holidays/", views.holiday_list, name="holiday_list"),
    path("holidays/create/", views.create_holiday, name="create_holiday"),
    path("holidays/<int:holiday_id>/delete/", views.delete_holiday, name="delete_holiday"),
    path("calendar/", views.calendar_feed, name="calendar"),
    path("calendar/events/", views.scheduler_events_feed, name="scheduler_events"),
    path("calendar/day/<str:date>/", views.scheduler_day_timetable, name="scheduler_day_timetable"),
    path("calendar/export-daily/", views.export_daily_timetable, name="export_daily_timetable"),
]

urlpatterns += router.urls
