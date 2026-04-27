from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_center, name="report_center"),
    path("csv/", views.download_csv, name="download_csv"),
    path("excel/", views.download_excel, name="download_excel"),
]
