from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render

from members.models import Member

from .models import CatalogAttachment, Keyword, Patent, Project, Publication


def _member_filter(queryset, request):
    member_id = request.GET.get("member")
    if member_id and member_id.isdecimal():
        queryset = queryset.filter(members__id=int(member_id))
        member = Member.objects.filter(pk=int(member_id)).first()
    else:
        member = None
    return queryset.distinct(), member


@login_required
def project_list(request):
    items, member = _member_filter(Project.objects.prefetch_related("members", "attachments"), request)
    query = request.GET.get("q", "").strip()
    if query:
        items = items.filter(title__icontains=query)
    return render(request, "catalog/item_list.html", {
        "title": "项目", "kind": "project", "items": items, "member": member, "query": query,
    })


@login_required
def patent_list(request):
    items, member = _member_filter(Patent.objects.prefetch_related("members", "attachments"), request)
    query = request.GET.get("q", "").strip()
    if query:
        items = items.filter(title__icontains=query)
    return render(request, "catalog/item_list.html", {
        "title": "专利", "kind": "patent", "items": items, "member": member, "query": query,
    })


@login_required
def publication_list(request):
    items, member = _member_filter(
        Publication.objects.prefetch_related("keywords", "members", "attachments"), request
    )
    query = request.GET.get("q", "").strip()
    keyword_id = request.GET.get("keyword")
    if query:
        items = items.filter(title__icontains=query) | items.filter(authors__icontains=query)
    if keyword_id and keyword_id.isdecimal():
        items = items.filter(keywords__id=int(keyword_id))
    return render(request, "catalog/item_list.html", {
        "title": "论文文献", "kind": "publication", "items": items.distinct(),
        "member": member, "query": query, "keywords": Keyword.objects.all(),
        "selected_keyword": keyword_id or "",
    })


@login_required
def keyword_list(request):
    return render(request, "catalog/keyword_list.html", {"keywords": Keyword.objects.all()})


@login_required
def project_detail(request, pk):
    item = get_object_or_404(Project.objects.prefetch_related("members", "attachments"), pk=pk)
    return render(request, "catalog/item_detail.html", {"kind": "project", "item": item})


@login_required
def publication_detail(request, pk):
    item = get_object_or_404(
        Publication.objects.prefetch_related("members", "keywords", "attachments"), pk=pk
    )
    return render(request, "catalog/item_detail.html", {"kind": "publication", "item": item})


@login_required
def patent_detail(request, pk):
    item = get_object_or_404(Patent.objects.prefetch_related("members", "attachments"), pk=pk)
    return render(request, "catalog/item_detail.html", {"kind": "patent", "item": item})


@login_required
def download_attachment(request, pk):
    attachment = get_object_or_404(CatalogAttachment, pk=pk)
    if not attachment.file or not attachment.file.storage.exists(attachment.file.name):
        raise Http404("资料文件不存在。")
    return FileResponse(
        attachment.file.open("rb"), as_attachment=True, filename=attachment.title
    )
