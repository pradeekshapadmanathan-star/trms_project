from django.contrib import admin

from .models import Batch, FileUpload, Holiday, Task

admin.site.register(Task)
admin.site.register(FileUpload)
admin.site.register(Batch)
admin.site.register(Holiday)
