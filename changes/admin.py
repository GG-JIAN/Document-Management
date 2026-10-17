from django.contrib import admin
from django.contrib.admin.models import LogEntry

from .models import ChangeRequest


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("request_type", "member", "requester", "status", "submitted_at", "reviewer", "reviewed_at")
    list_filter = ("status", "submitted_at")
    search_fields = ("member__name", "requester__username", "request_note")
    readonly_fields = tuple(field.name for field in ChangeRequest._meta.fields)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == "admin":
            return queryset
        return queryset.none()

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == "admin"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(LogEntry)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ("action_time", "user", "content_type", "object_repr", "action_flag")
    list_filter = ("action_flag", "content_type", "action_time")
    search_fields = ("user__username", "object_repr", "change_message")
    date_hierarchy = "action_time"
    ordering = ("-action_time",)
    readonly_fields = tuple(field.name for field in LogEntry._meta.fields)

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset.select_related("user", "content_type")
        return queryset.none()
