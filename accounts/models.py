from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "超级管理员"
        ADMIN = "admin", "管理员"
        MEMBER = "member", "普通用户"

    role = models.CharField(
        "用户权限级别", max_length=20, choices=Role.choices, default=Role.MEMBER,
        help_text="权限由系统角色统一管理，不使用单项英文权限勾选。",
    )
    member = models.OneToOneField(
        "members.Member",
        verbose_name="绑定课题组成员档案",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="account",
        help_text="管理员或超级管理员可设置；用户名须与成员姓名完全一致，一个成员档案只能绑定一个账号。",
    )

    def __str__(self):
        return self.member.name if self.member_id else self.username

    def clean(self):
        super().clean()
        if self.member_id and self.username != self.member.name:
            raise ValidationError({"username": "绑定成员时，用户名必须与成员姓名完全一致。"})
        if self.role == self.Role.SUPER_ADMIN and not self.is_superuser:
            raise ValidationError({"role": "超级管理员账号必须通过 createsuperuser 创建。"})

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.SUPER_ADMIN
            self.is_staff = True
        else:
            self.is_staff = self.role == self.Role.ADMIN
            if self.role == self.Role.ADMIN:
                self.member = None
        super().save(*args, **kwargs)

