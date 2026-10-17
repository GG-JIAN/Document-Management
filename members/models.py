from django.db import models


class Member(models.Model):
    name = models.CharField("姓名", max_length=80, unique=True)
    identity = models.CharField("身份", max_length=100, blank=True)
    email = models.EmailField("邮箱", blank=True)
    phone = models.CharField("联系方式", max_length=40, blank=True)
    research_topic = models.TextField("在跟课题", blank=True)
    is_active = models.BooleanField("在组", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "课题组成员"
        verbose_name_plural = "课题组成员"

    def __str__(self):
        return self.name

