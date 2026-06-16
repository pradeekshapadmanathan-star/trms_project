from django.db.models.signals import post_save
from django.dispatch import receiver

from tasks.models import TaskAssignment
from .models import Notification


@receiver(post_save, sender=TaskAssignment)
def create_task_assignment_notification(sender, instance, created, **kwargs):
    if not created:
        return
    Notification.objects.create(
        user=instance.assigned_to,
        message=f"New task assigned: {instance.task_name} (deadline {instance.deadline:%Y-%m-%d %H:%M})",
    )
