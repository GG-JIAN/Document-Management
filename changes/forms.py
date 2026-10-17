from django import forms
from django.conf import settings
from pathlib import Path

from members.models import Member
from catalog.utils import normalize_authors, split_keyword_names

MATERIAL_MAX_MB = settings.MAX_MATERIAL_UPLOAD_SIZE // (1024 * 1024)


class OptionalMaterialFileField(forms.FileField):
    def clean(self, data, initial=None):
        uploaded = super().clean(data, initial)
        if uploaded:
            extension = Path(uploaded.name).suffix.lower()
            allowed = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".png", ".jpg", ".jpeg"}
            if extension not in allowed:
                raise forms.ValidationError("仅支持 PDF、Office 文档、ZIP 或常见图片文件。")
            max_size = settings.MAX_MATERIAL_UPLOAD_SIZE
            if uploaded.size > max_size:
                raise forms.ValidationError(
                    f"单个资料文件不能超过 {max_size // (1024 * 1024)} MB。"
                )
        return uploaded


class MemberChangeRequestForm(forms.Form):
    identity = forms.CharField(label="身份", max_length=100, required=False)
    email = forms.EmailField(label="邮箱", required=False)
    phone = forms.CharField(label="联系方式", max_length=40, required=False)
    research_topic = forms.CharField(
        label="在跟课题", required=False, widget=forms.Textarea(attrs={"rows": 4})
    )
    request_note = forms.CharField(
        label="申请说明", required=False, widget=forms.Textarea(attrs={"rows": 3}), max_length=1000
    )

    @classmethod
    def from_member(cls, member, *args, **kwargs):
        initial = {
            "identity": member.identity,
            "email": member.email,
            "phone": member.phone,
            "research_topic": member.research_topic,
        }
        initial.update(kwargs.pop("initial", {}))
        return cls(*args, initial=initial, **kwargs)


class ReviewForm(forms.Form):
    decision = forms.ChoiceField(
        label="审核结果",
        choices=(("approved", "通过"), ("rejected", "驳回")),
    )
    review_note = forms.CharField(
        label="审核意见", required=False, max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class UploadProjectRequestForm(forms.Form):
    title = forms.CharField(label="项目名称", max_length=250)
    description = forms.CharField(label="项目简介", required=False, widget=forms.Textarea)
    status = forms.CharField(label="状态", max_length=80, required=False)
    start_date = forms.DateField(label="开始日期", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(label="结束日期", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    attachment = OptionalMaterialFileField(
        label="相关资料文件", required=False,
        help_text=f"单个文件最大 {MATERIAL_MAX_MB} MB；支持 PDF、Office 文档、ZIP 或常见图片文件。",
    )
    request_note = forms.CharField(label="申请说明", required=False, max_length=1000, widget=forms.Textarea)


class UploadPublicationRequestForm(forms.Form):
    title = forms.CharField(label="论文名称", max_length=500)
    authors = forms.CharField(
        label="作者", required=False, widget=forms.Textarea(attrs={"rows": 2}),
        help_text="多个作者可用顿号（、）或分号（; / ；）分隔。",
    )
    year = forms.IntegerField(label="年份", required=False, min_value=1, max_value=9999)
    venue = forms.CharField(label="期刊或会议", max_length=250, required=False)
    doi = forms.CharField(label="DOI", max_length=200, required=False)
    abstract = forms.CharField(label="摘要", required=False, widget=forms.Textarea(attrs={"rows": 4}))
    keywords = forms.CharField(
        label="关键词", required=True,
        help_text="必填。多个关键词用逗号、顿号或分号分隔；关键词会自动分别加入分类。",
    )
    attachment = OptionalMaterialFileField(
        label="论文文件或相关资料", required=False,
        help_text=f"单个文件最大 {MATERIAL_MAX_MB} MB；支持 PDF、Office 文档、ZIP 或常见图片文件。",
    )
    request_note = forms.CharField(label="申请说明", required=False, max_length=1000, widget=forms.Textarea)

    def clean_authors(self):
        return normalize_authors(self.cleaned_data.get("authors", ""))

    def clean_keywords(self):
        value = self.cleaned_data.get("keywords", "")
        names = split_keyword_names(value)
        if getattr(self, "require_keywords", True) and not names:
            raise forms.ValidationError("请至少填写一个关键词，文献将按这些关键词自动分类。")
        return ",".join(names)


class UpdatePublicationRequestForm(UploadPublicationRequestForm):
    """Publication fields to propose as the replacement values for an existing paper."""

    keywords = forms.CharField(
        label="关键词", required=False,
        help_text="多个关键词用逗号、顿号或分号分隔；留空表示清除原有关键词。",
    )
    require_keywords = False


class UploadPatentRequestForm(forms.Form):
    title = forms.CharField(label="专利名称", max_length=500)
    patent_number = forms.CharField(label="专利号", max_length=100, required=False)
    status = forms.CharField(label="状态", max_length=80, required=False)
    application_date = forms.DateField(label="申请日期", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    attachment = OptionalMaterialFileField(
        label="专利文件或相关资料", required=False,
        help_text=f"单个文件最大 {MATERIAL_MAX_MB} MB；支持 PDF、Office 文档、ZIP 或常见图片文件。",
    )
    request_note = forms.CharField(label="申请说明", required=False, max_length=1000, widget=forms.Textarea)
