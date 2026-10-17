from django.db import models


class MaterialCategory(models.Model):
    name = models.CharField("材料分类", max_length=120, unique=True)
    sort_order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        ordering = ("sort_order", "name")
        verbose_name = "材料分类"
        verbose_name_plural = "材料分类"

    def __str__(self):
        return self.name


class Material(models.Model):
    name = models.CharField("材料名称", max_length=300)
    category = models.ForeignKey(
        MaterialCategory, verbose_name="材料分类", on_delete=models.PROTECT,
        related_name="materials",
    )
    notes = models.TextField("特殊备注", blank=True)
    references = models.TextField("引用文献", blank=True)
    source_row = models.PositiveIntegerField("来源表格行", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ("category__sort_order", "name")
        constraints = [
            models.UniqueConstraint(fields=("category", "name"), name="unique_material_per_category")
        ]
        verbose_name = "材料"
        verbose_name_plural = "材料"

    def __str__(self):
        return self.name


class MaterialCharacteristic(models.Model):
    name = models.CharField("特性条目名称", max_length=180, unique=True)
    sort_order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        ordering = ("sort_order", "name")
        verbose_name = "材料特性条目"
        verbose_name_plural = "材料特性条目"

    def __str__(self):
        return self.name


class MaterialFeature(models.Model):
    material = models.ForeignKey(
        Material, verbose_name="材料", on_delete=models.CASCADE, related_name="features"
    )
    name = models.CharField("特性条目", max_length=180)
    condition = models.TextField("实验条件", blank=True)
    result = models.TextField("实验结果或数据", blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        ordering = ("sort_order", "id")
        verbose_name = "材料特性数据"
        verbose_name_plural = "材料特性数据"

    def __str__(self):
        return f"{self.material.name} · {self.name}"
