from django.conf import settings
from django.db import models


class ChangeRequest(models.Model):
    class RequestType(models.TextChoices):
        PROFILE_UPDATE = "profile_update", "成员资料修改"
        PROJECT_CREATE = "project_create", "新增项目"
        PUBLICATION_CREATE = "publication_create", "新增论文"
        PUBLICATION_UPDATE = "publication_update", "修改已收录论文"
        PATENT_CREATE = "patent_create", "新增专利"

    class Status(models.TextChoices):
        PENDING = "pending", "待审核"
        APPROVED = "approved", "已通过"
        REJECTED = "rejected", "已驳回"

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="申请人",
        on_delete=models.PROTECT,
        related_name="change_requests",
    )
    member = models.ForeignKey(
        "members.Member",
        verbose_name="关联成员",
        on_delete=models.PROTECT,
        related_name="change_requests",
    )
    target_publication = models.ForeignKey(
        "catalog.Publication",
        verbose_name="待修改论文",
        on_delete=models.PROTECT,
        related_name="change_requests",
        null=True,
        blank=True,
    )
    request_type = models.CharField(
        "申请类型",
        max_length=30,
        choices=RequestType.choices,
        default=RequestType.PROFILE_UPDATE,
    )
    payload = models.JSONField("申请内容", default=dict)
    attachment = models.FileField(
        "申请附件", upload_to="pending_attachments/%Y/%m/", blank=True
    )
    request_note = models.TextField("申请说明", blank=True)
    status = models.CharField(
        "审核状态", max_length=20, choices=Status.choices, default=Status.PENDING
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="审核人",
        on_delete=models.PROTECT,
        related_name="reviewed_change_requests",
        null=True,
        blank=True,
    )
    review_note = models.TextField("审核意见", blank=True)
    submitted_at = models.DateTimeField("提交时间", auto_now_add=True)
    reviewed_at = models.DateTimeField("审核时间", null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "成员资料变更申请"
        verbose_name_plural = "成员资料变更申请"

    def __str__(self):
        return f"{self.member.name}的资料变更申请（{self.get_status_display()}）"
