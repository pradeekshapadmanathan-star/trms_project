from rest_framework import permissions, viewsets

from .models import ScheduleSlot, TaskAssignment
from .serializers import ScheduleSlotSerializer, TaskAssignmentSerializer


class RolePermission(permissions.BasePermission):
    allowed_roles = {"admin", "manager", "circle_lead", "trainer"}

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in self.allowed_roles)


class TaskAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TaskAssignment.objects.select_related("assigned_by", "assigned_to")
    serializer_class = TaskAssignmentSerializer
    permission_classes = [RolePermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == "trainer":
            return queryset.filter(assigned_to=self.request.user)
        if self.request.user.role == "circle_lead":
            return queryset.filter(assigned_to__trainer_profile__circle__manager=self.request.user)
        return queryset


class ScheduleSlotViewSet(viewsets.ModelViewSet):
    queryset = ScheduleSlot.objects.select_related("trainer", "batch")
    serializer_class = ScheduleSlotSerializer
    permission_classes = [RolePermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == "trainer":
            return queryset.filter(trainer=self.request.user)
        if self.request.user.role == "circle_lead":
            return queryset.filter(trainer__trainer_profile__circle__manager=self.request.user)
        return queryset
