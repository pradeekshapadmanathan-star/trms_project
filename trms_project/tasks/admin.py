from django.contrib import admin

from .models import Batch, DailyTracker, FileUpload, Holiday, ScheduleSlot, Task, TaskAssignment

admin.site.register(Task)
admin.site.register(FileUpload)
admin.site.register(Batch)
admin.site.register(Holiday)
admin.site.register(ScheduleSlot)
admin.site.register(TaskAssignment)
admin.site.register(DailyTracker)
