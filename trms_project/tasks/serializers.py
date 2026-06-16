from rest_framework import serializers

from .models import ScheduleSlot, TaskAssignment


class TaskAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAssignment
        fields = [
            "id",
            "task_name",
            "description",
            "assigned_by",
            "assigned_to",
            "task_type",
            "priority",
            "deadline",
            "status",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class ScheduleSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleSlot
        fields = [
            "id",
            "trainer",
            "batch",
            "task_type",
            "date",
            "start_time",
            "end_time",
            "status_color",
            "occupancy_status",
        ]
