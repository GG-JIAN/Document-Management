from django.contrib import admin

from accounts.permissions import can_manage_records
from .models import Material, MaterialCategory, MaterialFeature


class ManagerOnlyAdmin:
    def has_view_permission(self, request, obj=None):
        return can_manage_records(request.user)

    def has_add_permission(self, request):
        return can_manage_records(request.user)

    def has_change_permission(self, request, obj=None):
        return can_manage_records(request.user)

    def has_delete_permission(self, request, obj=None):
        return can_manage_records(request.user)


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(ManagerOnlyAdmin, admin.ModelAdmin):
    list_display = ("name", "sort_order", "material_count")
    search_fields = ("name",)
    ordering = ("sort_order", "name")

    @admin.display(description="材料数")
    def material_count(self, obj):
        return obj.materials.count()


class MaterialFeatureInline(admin.TabularInline):
    model = MaterialFeature
    extra = 1
    ordering = ("sort_order", "id")
    fields = ("name", "condition", "result", "sort_order")


@admin.register(Material)
class MaterialAdmin(ManagerOnlyAdmin, admin.ModelAdmin):
    list_display = ("name", "category", "feature_count", "updated_at")
    list_filter = ("category",)
    search_fields = (
        "name", "category__name", "notes", "references",
        "features__name", "features__condition", "features__result",
    )
    autocomplete_fields = ("category",)
    inlines = (MaterialFeatureInline,)
    list_per_page = 50

    @admin.display(description="特性条目数")
    def feature_count(self, obj):
        return obj.features.count()


@admin.register(MaterialFeature)
class MaterialFeatureAdmin(ManagerOnlyAdmin, admin.ModelAdmin):
    list_display = ("material", "name", "sort_order")
    list_filter = ("material__category",)
    search_fields = ("material__name", "name", "condition", "result")
    autocomplete_fields = ("material",)
    list_per_page = 50
