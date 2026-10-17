import re

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from pypinyin import lazy_pinyin

from catalog.models import Patent, Project, Publication
from .models import Member


def _member_sort_key(member):
    identity = (member.identity or "").strip()
    name_pinyin = "".join(lazy_pinyin(member.name, errors="ignore")).casefold()
    if "导师" in identity:
        return (0, 0, 0, name_pinyin)
    if "博士" in identity:
        group = 1
    elif "硕士" in identity:
        group = 2
    else:
        return (3, 0, 0, name_pinyin)

    match = re.search(r"(?:19|20)\d{2}", identity)
    if match:
        return (group, 0, int(match.group()), name_pinyin)
    return (group, 1, 0, name_pinyin)


@login_required
def member_list(request):
    query = request.GET.get("q", "").strip()
    members = Member.objects.filter(is_active=True).annotate(
        project_count=Count("projects", distinct=True),
        publication_count=Count("publications", distinct=True),
        patent_count=Count("patents", distinct=True),
    )
    if query:
        members = members.filter(
            Q(name__icontains=query)
            | Q(identity__icontains=query)
            | Q(research_topic__icontains=query)
        )
    members = sorted(members, key=_member_sort_key)
    return render(request, "members/member_list.html", {
        "members": members,
        "member_total": Member.objects.filter(is_active=True).count(),
        "project_total": Project.objects.count(),
        "publication_total": Publication.objects.count(),
        "patent_total": Patent.objects.count(),
    })


@login_required
def member_detail(request, pk):
    member = get_object_or_404(Member, pk=pk, is_active=True)
    member.project_count = member.projects.count()
    member.publication_count = member.publications.count()
    member.patent_count = member.patents.count()
    return render(request, "members/member_detail.html", {"member": member})


