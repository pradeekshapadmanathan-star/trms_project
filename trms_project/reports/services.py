from io import BytesIO

import pandas as pd
from django.db.models import Sum

from accounts.models import User
from tasks.services import MONTHLY_CAPACITY, calculate_occupancy
from tasks.models import Task


def generate_monthly_report(month):
    year = month.year
    month_num = month.month
    rows = []
    trainers = User.objects.filter(role=User.Role.TRAINER).order_by("name")
    for trainer in trainers:
        tasks = Task.objects.filter(trainer=trainer, date__year=year, date__month=month_num)
        totals = tasks.aggregate(total=Sum("hours"))
        breakdown = {
            task_type: float(
                tasks.filter(task_type=task_type).aggregate(total=Sum("hours")).get("total") or 0
            )
            for task_type, _ in Task.TaskType.choices
        }
        occupancy = calculate_occupancy(trainer, year, month_num)
        rows.append(
            {
                "trainer_name": trainer.name,
                "total_hours": float(totals.get("total") or 0),
                "task_breakdown": ", ".join(f"{key}: {value}h" for key, value in breakdown.items()),
                "occupancy_percent": occupancy["occupancy_percent"],
                "remaining_hours": occupancy["remaining_hours"],
                "monthly_capacity": float(MONTHLY_CAPACITY),
            }
        )
    return pd.DataFrame(rows)


def dataframe_to_excel_bytes(dataframe):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Monthly Report")
    return buffer.getvalue()
