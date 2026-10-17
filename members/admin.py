from django.contrib import admin

from accounts.permissions import can_manage_records
from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("name", "identity", "email", "phone", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "identity", "research_topic", "email")
    ordering = ("name",)

    def has_view_permission(self, request, obj=None):
        return can_manage_records(request.user)

    def has_add_permission(self, request):
        return can_manage_records(request.user)

    def has_change_permission(self, request, obj=None):
        return can_manage_records(request.user)

    def has_delete_permission(self, request, obj=None):
        return can_manage_records(request.user)

