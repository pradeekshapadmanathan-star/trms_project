from django import forms

from .models import Batch, FileUpload, Holiday, Task


class DateInput(forms.DateInput):
    input_type = "date"


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["trainer", "date", "task_type", "hours", "description", "status"]
        widgets = {
            "date": DateInput(),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class FileUploadForm(forms.ModelForm):
    class Meta:
        model = FileUpload
        fields = ["file"]


class BatchForm(forms.ModelForm):
    assessment_dates = forms.CharField(
        required=False,
        help_text="Comma-separated dates in YYYY-MM-DD format.",
        widget=forms.TextInput(attrs={"placeholder": "2026-04-30, 2026-05-15"}),
    )

    class Meta:
        model = Batch
        fields = ["name", "course", "start_date", "end_date", "trainer", "circle", "holidays", "assessment_dates"]
        widgets = {
            "start_date": DateInput(),
            "end_date": DateInput(),
            "holidays": forms.SelectMultiple(attrs={"size": 5}),
        }

    def clean_assessment_dates(self):
        raw_dates = self.cleaned_data["assessment_dates"]
        if not raw_dates:
            return []
        return [item.strip() for item in raw_dates.split(",") if item.strip()]


class HolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ["date", "description"]
        widgets = {"date": DateInput()}
