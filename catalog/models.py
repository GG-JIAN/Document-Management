from django.db import models


class Keyword(models.Model):
    name = models.CharField("关键词", max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "文献关键词"
        verbose_name_plural = "文献关键词"

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField("项目名称", max_length=250)
    description = models.TextField("项目简介", blank=True)
    status = models.CharField("状态", max_length=80, blank=True)
    start_date = models.DateField("开始日期", null=True, blank=True)
    end_date = models.DateField("结束日期", null=True, blank=True)
    members = models.ManyToManyField(
        "members.Member", verbose_name="参与成员", related_name="projects", blank=True
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "项目"
        verbose_name_plural = "项目"

    def __str__(self):
        return self.title


class Publication(models.Model):
    title = models.CharField("论文名称", max_length=500)
    authors = models.TextField("作者", blank=True, help_text="按论文原始顺序填写作者")
    year = models.PositiveSmallIntegerField("年份", null=True, blank=True)
    venue = models.CharField("期刊或会议", max_length=250, blank=True)
    doi = models.CharField("DOI", max_length=200, blank=True)
    abstract = models.TextField("摘要", blank=True)
    members = models.ManyToManyField(
        "members.Member", verbose_name="组内作者", related_name="publications", blank=True
    )
    keywords = models.ManyToManyField(
        Keyword, verbose_name="关键词", related_name="publications", blank=True
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["-year", "title"]
        verbose_name = "论文文献"
        verbose_name_plural = "论文文献"

    def __str__(self):
        return self.title


class Patent(models.Model):
    title = models.CharField("专利名称", max_length=500)
    patent_number = models.CharField("专利号", max_length=100, blank=True)
    status = models.CharField("状态", max_length=80, blank=True)
    application_date = models.DateField("申请日期", null=True, blank=True)
    members = models.ManyToManyField(
        "members.Member", verbose_name="组内发明人", related_name="patents", blank=True
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "专利"
        verbose_name_plural = "专利"

    def __str__(self):
        return self.title


class CatalogAttachment(models.Model):
    title = models.CharField("资料名称", max_length=255)
    file = models.FileField("资料文件", upload_to="catalog_attachments/%Y/%m/")
    content_sha256 = models.CharField("文件校验值", max_length=64, blank=True, db_index=True)
    project = models.ForeignKey(
        Project, verbose_name="所属项目", on_delete=models.CASCADE,
        related_name="attachments", null=True, blank=True,
    )
    publication = models.ForeignKey(
        Publication, verbose_name="所属论文", on_delete=models.CASCADE,
        related_name="attachments", null=True, blank=True,
    )
    patent = models.ForeignKey(
        Patent, verbose_name="所属专利", on_delete=models.CASCADE,
        related_name="attachments", null=True, blank=True,
    )
    uploaded_by = models.ForeignKey(
        "accounts.User", verbose_name="上传人", on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    created_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "项目、论文或专利资料"
        verbose_name_plural = "项目、论文或专利资料"

    def __str__(self):
        return self.title
