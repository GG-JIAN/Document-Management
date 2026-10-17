from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from .forms import (
    MemberChangeRequestForm,
    ReviewForm,
    UpdatePublicationRequestForm,
    UploadPatentRequestForm,
    UploadProjectRequestForm,
    UploadPublicationRequestForm,
)
from .models import ChangeRequest
from .services import PROFILE_FIELDS, log_request_submission, review_request


def _is_reviewer(user):
    return user.is_superuser or user.role == User.Role.ADMIN


@login_required
def request_list(request):
    if _is_reviewer(request.user):
        requests = ChangeRequest.objects.select_related("requester", "member", "reviewer")
    else:
        requests = ChangeRequest.objects.filter(requester=request.user).select_related(
            "member", "reviewer"
        )
    return render(request, "changes/request_list.html", {"change_requests": requests})


@login_required
def download_request_attachment(request, pk):
    change_request = get_object_or_404(ChangeRequest, pk=pk)
    if not (_is_reviewer(request.user) or change_request.requester_id == request.user.pk):
        raise PermissionDenied("无权查看此申请附件。")
    if not change_request.attachment or not change_request.attachment.storage.exists(change_request.attachment.name):
        raise Http404("申请附件不存在。")
    filename = change_request.attachment.name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    return FileResponse(change_request.attachment.open("rb"), as_attachment=True, filename=filename)


@login_required
def create_member_request(request):
    member = request.user.member
    if member is None or not member.is_active:
        raise PermissionDenied("账号尚未由超级管理员绑定到有效的课题组成员。")

    if request.method == "POST":
        form = MemberChangeRequestForm.from_member(member, request.POST)
        if form.is_valid():
            values = form.cleaned_data
            change_request = ChangeRequest.objects.create(
                requester=request.user,
                member=member,
                request_type=ChangeRequest.RequestType.PROFILE_UPDATE,
                payload={field: values[field] for field in PROFILE_FIELDS},
                request_note=values["request_note"],
            )
            log_request_submission(change_request)
            messages.success(request, "申请已提交，审核通过后资料才会更新。")
            return redirect("changes:list")
    else:
        form = MemberChangeRequestForm.from_member(member)
    return render(request, "changes/request_form.html", {"form": form, "member": member})


UPLOAD_REQUESTS = {
    "project": (ChangeRequest.RequestType.PROJECT_CREATE, UploadProjectRequestForm, "申请新增项目"),
    "publication": (ChangeRequest.RequestType.PUBLICATION_CREATE, UploadPublicationRequestForm, "申请新增论文"),
    "patent": (ChangeRequest.RequestType.PATENT_CREATE, UploadPatentRequestForm, "申请新增专利"),
}


@login_required
def create_upload_request(request, kind):
    if kind not in UPLOAD_REQUESTS:
        raise PermissionDenied("不支持的资料类型。")
    if _is_reviewer(request.user):
        raise PermissionDenied("管理员请直接在管理后台添加正式资料。")
    member = request.user.member
    if member is None or not member.is_active:
        raise PermissionDenied("账号尚未由超级管理员绑定到有效的课题组成员。")

    request_type, form_class, title = UPLOAD_REQUESTS[kind]
    form = form_class(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        cleaned = form.cleaned_data
        payload = {}
        for key, value in cleaned.items():
            if key in {"request_note", "attachment"}:
                continue
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            if key == "keywords":
                value = [part for part in value.split(",") if part]
            payload[key] = value
        change_request = ChangeRequest.objects.create(
            requester=request.user,
            member=member,
            request_type=request_type,
            payload=payload,
            attachment=cleaned.get("attachment"),
            request_note=cleaned["request_note"],
        )
        log_request_submission(change_request)
        messages.success(request, "资料申请已提交，审核通过后会出现在正式列表中。")
        return redirect("changes:list")

    return render(request, "changes/upload_request_form.html", {
        "form": form, "member": member, "title": title,
    })


@login_required
def create_publication_update_request(request, pk):
    if _is_reviewer(request.user):
        raise PermissionDenied("管理员请直接在管理后台修改论文资料。")
    member = request.user.member
    if member is None or not member.is_active:
        raise PermissionDenied("账号尚未绑定到有效的课题组成员。")
    publication = member.publications.filter(pk=pk).first()
    if publication is None:
        raise PermissionDenied("只能申请修改自己成员档案关联的论文。")

    initial = {
        "title": publication.title,
        "authors": publication.authors,
        "year": publication.year,
        "venue": publication.venue,
        "doi": publication.doi,
        "abstract": publication.abstract,
        "keywords": ", ".join(publication.keywords.values_list("name", flat=True)),
    }
    form = UpdatePublicationRequestForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        cleaned = form.cleaned_data
        payload = {
            key: value for key, value in cleaned.items()
            if key not in {"request_note", "attachment"}
        }
        payload["keywords"] = [part for part in payload["keywords"].split(",") if part]
        change_request = ChangeRequest.objects.create(
            requester=request.user,
            member=member,
            target_publication=publication,
            request_type=ChangeRequest.RequestType.PUBLICATION_UPDATE,
            payload=payload,
            attachment=cleaned.get("attachment"),
            request_note=cleaned["request_note"],
        )
        log_request_submission(change_request)
        messages.success(request, "论文修改申请已提交，审核通过后将更新该论文。")
        return redirect("changes:list")

    return render(request, "changes/upload_request_form.html", {
        "form": form,
        "member": member,
        "title": f"申请修改论文：{publication.title}",
    })


@login_required
@require_POST
def review_member_request(request, pk):
    if not _is_reviewer(request.user):
        raise PermissionDenied("只有管理员或超级管理员可以审核申请。")
    form = ReviewForm(request.POST)
    if form.is_valid():
        try:
            review_request(
                change_request_id=pk,
                reviewer=request.user,
                decision=form.cleaned_data["decision"],
                review_note=form.cleaned_data["review_note"],
            )
        except (ChangeRequest.DoesNotExist, ValidationError) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "申请已处理。")
    else:
        messages.error(request, "审核表单无效。")
    return redirect("changes:list")
