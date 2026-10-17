from django.contrib import admin
from django import forms

from accounts.permissions import can_manage_records
from .utils import normalize_authors
from .models import CatalogAttachment, Keyword, Patent, Project, Publication


class CatalogAttachmentInline(admin.TabularInline):
    model = CatalogAttachment
    extra = 0
    fields = ("title", "file", "uploaded_by", "created_at")
    readonly_fields = ("created_at",)

    def has_delete_permission(self, request, obj=None):
        return can_manage_records(request.user)


class PublicationAdminForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = "__all__"

    def clean_title(self):
        title = self.cleaned_data["title"]
        normalized = " ".join(title.split()).casefold()
        current_title = " ".join((self.instance.title or "").split()).casefold()
        if self.instance.pk and normalized == current_title:
            return title
        for existing in Publication.objects.exclude(pk=self.instance.pk):
            if " ".join(existing.title.split()).casefold() == normalized:
                raise forms.ValidationError(
                    f"已存在同名文献“{existing.title}”。请编辑该条目并补充成员或关键词，避免重复建档。"
                )
        return title

    def clean_authors(self):
        return normalize_authors(self.cleaned_data.get("authors", ""))


class RecordAdminPermissions:
    def has_view_permission(self, request, obj=None):
        return can_manage_records(request.user)

    def has_add_permission(self, request):
        return can_manage_records(request.user)

    def has_change_permission(self, request, obj=None):
        return can_manage_records(request.user)

    def has_delete_permission(self, request, obj=None):
        return can_manage_records(request.user)


@admin.register(Keyword)
class KeywordAdmin(RecordAdminPermissions, admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Project)
class ProjectAdmin(RecordAdminPermissions, admin.ModelAdmin):
    list_display = ("title", "status", "start_date", "end_date")
    list_filter = ("status",)
    search_fields = ("title", "description", "members__name")
    filter_horizontal = ("members",)
    inlines = (CatalogAttachmentInline,)


@admin.register(Publication)
class PublicationAdmin(RecordAdminPermissions, admin.ModelAdmin):
    form = PublicationAdminForm
    list_display = ("title", "year", "venue", "doi")
    list_filter = ("year", "keywords")
    search_fields = ("title", "authors", "venue", "doi", "members__name")
    filter_horizontal = ("members", "keywords")
    inlines = (CatalogAttachmentInline,)

    class Media:
        js = ("catalog/admin_publication.js",)


@admin.register(Patent)
class PatentAdmin(RecordAdminPermissions, admin.ModelAdmin):
    list_display = ("title", "patent_number", "status", "application_date")
    list_filter = ("status",)
    search_fields = ("title", "patent_number", "members__name")
    filter_horizontal = ("members",)
    inlines = (CatalogAttachmentInline,)

