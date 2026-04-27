from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from tasks import views as task_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("schedule/<str:date>/", task_views.get_schedule_by_date, name="schedule_by_date"),
    path("", include("dashboard.urls")),
    path("tasks/", include("tasks.urls")),
    path("reports/", include("reports.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
