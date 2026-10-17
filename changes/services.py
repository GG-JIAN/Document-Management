from django.core.exceptions import ValidationError
from django.core.files import File
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from catalog.models import CatalogAttachment, Patent, Project, Publication, Keyword
from catalog.utils import normalize_authors, split_keyword_names

from .models import ChangeRequest

PROFILE_FIELDS = ("identity", "email", "phone", "research_topic")


@transaction.atomic
def review_request(*, change_request_id, reviewer, decision, review_note=""):
    request = ChangeRequest.objects.select_for_update().select_related("member").get(
        pk=change_request_id
    )
    if request.status != ChangeRequest.Status.PENDING:
        raise ValidationError("该申请已经审核，不能重复处理。")

    if decision == ChangeRequest.Status.APPROVED:
        _apply_request(request)
    elif decision != ChangeRequest.Status.REJECTED:
        raise ValidationError("无效的审核结果。")

    request.status = decision
    request.reviewer = reviewer
    request.review_note = review_note
    request.reviewed_at = timezone.now()
    request.save(update_fields=("status", "reviewer", "review_note", "reviewed_at", "attachment"))
    LogEntry.objects.log_action(
        user_id=reviewer.pk,
        content_type_id=ContentType.objects.get_for_model(ChangeRequest).pk,
        object_id=request.pk,
        object_repr=str(request),
        action_flag=CHANGE,
        change_message=f"审核结果：{request.get_status_display()}。{review_note}".strip(),
    )
    return request


def log_request_submission(change_request):
    LogEntry.objects.log_action(
        user_id=change_request.requester_id,
        content_type_id=ContentType.objects.get_for_model(ChangeRequest).pk,
        object_id=change_request.pk,
        object_repr=str(change_request),
        action_flag=ADDITION,
        change_message=f"提交{change_request.get_request_type_display()}申请。",
    )


def _require_payload_fields(request, expected):
    if set(request.payload) != set(expected):
        raise ValidationError("申请内容不完整或包含不允许提交的字段。")


def _parse_date(value):
    from datetime import date

    return date.fromisoformat(value) if value else None


def _apply_request(request):
    payload = request.payload
    if request.request_type == ChangeRequest.RequestType.PROFILE_UPDATE:
        _require_payload_fields(request, PROFILE_FIELDS)
        for field in PROFILE_FIELDS:
            setattr(request.member, field, payload[field])
        request.member.save()
        return

    if request.request_type == ChangeRequest.RequestType.PROJECT_CREATE:
        fields = ("title", "description", "status", "start_date", "end_date")
        _require_payload_fields(request, fields)
        item = _find_by_title(Project, payload["title"])
        if item is None:
            item = Project.objects.create(
                title=payload["title"],
                description=payload["description"],
                status=payload["status"],
                start_date=_parse_date(payload["start_date"]),
                end_date=_parse_date(payload["end_date"]),
            )
        else:
            _fill_missing(item, {
                "description": payload["description"],
                "status": payload["status"],
                "start_date": _parse_date(payload["start_date"]),
                "end_date": _parse_date(payload["end_date"]),
            })
        item.members.add(request.member)
        _save_attachment(request, project=item)
        return

    if request.request_type == ChangeRequest.RequestType.PUBLICATION_CREATE:
        fields = ("title", "authors", "year", "venue", "doi", "abstract", "keywords")
        _require_payload_fields(request, fields)
        item = _find_publication(payload)
        if item is None:
            item = Publication.objects.create(
                title=payload["title"],
                authors=normalize_authors(payload["authors"]),
                year=payload["year"] or None,
                venue=payload["venue"],
                doi=payload["doi"],
                abstract=payload["abstract"],
            )
        else:
            _fill_missing(item, {
                "authors": normalize_authors(payload["authors"]),
                "year": payload["year"] or None,
                "venue": payload["venue"],
                "doi": payload["doi"],
                "abstract": payload["abstract"],
            })
        item.members.add(request.member)
        for name in split_keyword_names(payload["keywords"]):
            keyword = _get_keyword(name)
            item.keywords.add(keyword)
        _save_attachment(request, publication=item)
        return

    if request.request_type == ChangeRequest.RequestType.PUBLICATION_UPDATE:
        fields = ("title", "authors", "year", "venue", "doi", "abstract", "keywords")
        _require_payload_fields(request, fields)
        publication = request.target_publication
        if publication is None or not publication.members.filter(pk=request.member_id).exists():
            raise ValidationError("待修改论文已不存在或已与申请成员解除关联。")
        publication.title = payload["title"]
        publication.authors = normalize_authors(payload["authors"])
        publication.year = payload["year"] or None
        publication.venue = payload["venue"]
        publication.doi = payload["doi"]
        publication.abstract = payload["abstract"]
        publication.save()
        keywords = [_get_keyword(name) for name in split_keyword_names(payload["keywords"])]
        publication.keywords.set(keywords)
        _save_attachment(request, publication=publication)
        return

    if request.request_type == ChangeRequest.RequestType.PATENT_CREATE:
        fields = ("title", "patent_number", "status", "application_date")
        _require_payload_fields(request, fields)
        item = _find_patent(payload)
        if item is None:
            item = Patent.objects.create(
                title=payload["title"],
                patent_number=payload["patent_number"],
                status=payload["status"],
                application_date=_parse_date(payload["application_date"]),
            )
        else:
            _fill_missing(item, {
                "patent_number": payload["patent_number"],
                "status": payload["status"],
                "application_date": _parse_date(payload["application_date"]),
            })
        item.members.add(request.member)
        _save_attachment(request, patent=item)
        return

    raise ValidationError("不支持的申请类型。")


def _save_attachment(request, *, project=None, publication=None, patent=None):
    if not request.attachment:
        return
    source_field = request.attachment
    digest = _file_sha256(source_field)
    target_filter = (
        {"project": project} if project is not None else
        {"publication": publication} if publication is not None else
        {"patent": patent}
    )
    for existing in CatalogAttachment.objects.filter(**target_filter):
        if not existing.content_sha256 and existing.file:
            try:
                existing.content_sha256 = _file_sha256(existing.file)
                existing.save(update_fields=("content_sha256",))
            except OSError:
                continue
        if existing.content_sha256 == digest:
            _discard_request_file_after_commit(request)
            return

    title = source_field.name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    attachment = CatalogAttachment(
        title=title,
        content_sha256=digest,
        uploaded_by=request.requester,
        **target_filter,
    )
    with source_field.open("rb") as source:
        attachment.file.save(attachment.title, File(source), save=True)
    _discard_request_file_after_commit(request)


def _discard_request_file_after_commit(request):
    storage = request.attachment.storage
    name = request.attachment.name
    request.attachment = ""
    transaction.on_commit(lambda: storage.delete(name))


def _file_sha256(field_file):
    import hashlib

    digest = hashlib.sha256()
    with field_file.open("rb") as source:
        for chunk in source.chunks():
            digest.update(chunk)
    return digest.hexdigest()


def _get_keyword(name):
    keyword = Keyword.objects.filter(name__iexact=name).first()
    if keyword is not None:
        return keyword
    return Keyword.objects.create(name=name)


def _normalized_text(value):
    return " ".join((value or "").split()).casefold()


def _find_by_title(model, title):
    normalized = _normalized_text(title)
    return next((item for item in model.objects.all() if _normalized_text(item.title) == normalized), None)


def _normalized_doi(value):
    doi = (value or "").strip().casefold()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi.strip()


def _find_publication(payload):
    title = _normalized_text(payload["title"])
    incoming_doi = _normalized_doi(payload["doi"])
    publications = list(Publication.objects.all())
    for publication in publications:
        if _normalized_text(publication.title) == title:
            return publication
    for publication in publications:
        if incoming_doi and _normalized_doi(publication.doi) == incoming_doi:
            return publication
    return None


def _find_patent(payload):
    patent_number = _normalized_text(payload["patent_number"])
    if patent_number:
        for patent in Patent.objects.all():
            if _normalized_text(patent.patent_number) == patent_number:
                return patent
    return _find_by_title(Patent, payload["title"])


def _fill_missing(instance, values):
    changed = []
    for field, value in values.items():
        if value not in (None, "") and getattr(instance, field) in (None, ""):
            setattr(instance, field, value)
            changed.append(field)
    if changed:
        instance.save(update_fields=changed)
