from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils.html import format_html

from .models import User

admin.site.unregister(Group)


@admin.register(User)
class LabUserAdmin(UserAdmin):
    list_display = ("username", "role", "member", "is_active")
    list_filter = ("role", "is_active")

    @admin.display(description="密码管理")
    def password_reset_link(self, obj):
        url = reverse("admin:auth_user_password_change", args=(obj.pk,))
        return format_html('<a class="button" href="{}">设置新密码</a>', url)

    def user_change_password(self, request, id, form_url=""):
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().user_change_password(request, id, form_url)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(role=User.Role.MEMBER, is_superuser=False)

    @admin.display(description="姓名 / 登录用户名")
    def display_name(self, obj):
        return obj.member.name if obj.member_id else obj.username

    def get_list_display(self, request):
        columns = ("display_name", "role", "member", "is_active")
        if request.user.is_superuser:
            return (*columns, "password_reset_link")
        return columns

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            if obj is None:
                return (
                    ("登录信息", {"fields": ("username", "password1", "password2")}),
                    ("账号状态", {"fields": ("is_active",)}),
                    ("系统权限与成员绑定", {"fields": ("role", "member")}),
                )
            return (
                ("登录信息", {"fields": ("username", "password")}),
                ("账号状态", {"fields": ("is_active",)}),
                ("系统权限与成员绑定", {"fields": ("role", "member")}),
            )
        if obj is None:
            return (
                (None, {"fields": ("username", "password1", "password2")}),
                ("账号状态", {"fields": ("is_active",)}),
                ("课题组成员绑定", {"fields": ("member",)}),
            )
        return (
            (None, {"fields": ("username",)}),
            ("账号状态", {"fields": ("is_active",)}),
            ("课题组成员绑定", {"fields": ("member",)}),
        )

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser and obj is not None and obj.pk == request.user.pk:
            return ("role",)
        return super().get_readonly_fields(request, obj)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "username":
            kwargs["label"] = "姓名 / 登录用户名"
            kwargs["help_text"] = "普通用户绑定成员时，必须与成员档案中的姓名完全一致。"
        elif db_field.name == "member":
            kwargs["label"] = "绑定课题组成员档案"
            kwargs["help_text"] = "管理员或超级管理员可设置；用户名须与成员姓名一致，一个成员档案只能绑定一个账号。"
        elif db_field.name == "role":
            kwargs["label"] = "用户权限级别"
            kwargs["help_text"] = "通过系统角色控制权限，不需要勾选单项权限。"
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == User.Role.ADMIN

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.role == User.Role.ADMIN

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.role != User.Role.ADMIN:
            return False
        return obj is None or (obj.role == User.Role.MEMBER and not obj.is_superuser)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.role != User.Role.ADMIN:
            return False
        return obj is None or (obj.role == User.Role.MEMBER and not obj.is_superuser)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.role = User.Role.MEMBER
            obj.is_superuser = False
        super().save_model(request, obj, form, change)

