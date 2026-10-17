from django.contrib import admin
from django import forms

from accounts.permissions import can_manage_records
from .models import Material, MaterialCategory, MaterialCharacteristic, MaterialFeature


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


class MaterialFeatureInlineForm(forms.ModelForm):
    name = forms.ModelChoiceField(
        label="特性条目",
        queryset=MaterialCharacteristic.objects.none(),
        empty_label="请选择特性条目",
    )

    class Meta:
        model = MaterialFeature
        fields = ("name", "condition", "result", "sort_order")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].queryset = MaterialCharacteristic.objects.order_by("sort_order", "name")
        if self.instance.pk:
            characteristic = MaterialCharacteristic.objects.filter(name=self.instance.name).first()
            if characteristic:
                self.initial["name"] = characteristic.pk

    def clean_name(self):
        characteristic = self.cleaned_data["name"]
        return characteristic.name


class MaterialFeatureInline(admin.TabularInline):
    model = MaterialFeature
    form = MaterialFeatureInlineForm
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


@admin.register(MaterialCharacteristic)
class MaterialCharacteristicAdmin(ManagerOnlyAdmin, admin.ModelAdmin):
    list_display = ("name", "sort_order")
    search_fields = ("name",)
    ordering = ("sort_order", "name")
    list_per_page = 100
