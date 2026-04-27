from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from accounts.decorators import role_required
from accounts.models import User
from .services import dataframe_to_excel_bytes, generate_monthly_report


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def report_center(request):
    month_value = request.GET.get("month") or datetime.today().strftime("%Y-%m")
    selected_month = datetime.strptime(f"{month_value}-01", "%Y-%m-%d").date()
    dataframe = generate_monthly_report(selected_month)
    table = dataframe.to_dict(orient="records")
    return render(request, "reports/report_center.html", {"rows": table, "month_value": month_value})


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def download_csv(request):
    month_value = request.GET.get("month") or datetime.today().strftime("%Y-%m")
    selected_month = datetime.strptime(f"{month_value}-01", "%Y-%m-%d").date()
    dataframe = generate_monthly_report(selected_month)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="trms-report-{month_value}.csv"'
    response.write(dataframe.to_csv(index=False))
    return response


@login_required
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def download_excel(request):
    month_value = request.GET.get("month") or datetime.today().strftime("%Y-%m")
    selected_month = datetime.strptime(f"{month_value}-01", "%Y-%m-%d").date()
    dataframe = generate_monthly_report(selected_month)
    response = HttpResponse(
        dataframe_to_excel_bytes(dataframe),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="trms-report-{month_value}.xlsx"'
    return response
