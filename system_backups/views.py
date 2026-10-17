from pathlib import Path
from io import StringIO

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST


def _require_superuser(user):
    if not user.is_superuser:
        raise PermissionDenied("只有超级管理员可以访问系统备份。")


@login_required
def backup_list(request):
    _require_superuser(request.user)
    backup_dir = Path(settings.BACKUP_DIR)
    files = []
    if backup_dir.exists():
        for path in sorted(backup_dir.glob("lab_backup_*.zip"), key=lambda item: item.stat().st_mtime, reverse=True):
            if path.is_file():
                stat = path.stat()
                files.append({"name": path.name, "size": stat.st_size, "modified": stat.st_mtime})
    return render(request, "system_backups/backup_list.html", {"backups": files})


@login_required
@require_POST
def backup_create(request):
    _require_superuser(request.user)
    output = StringIO()
    try:
        call_command("backup_system", stdout=output)
    except CommandError as exc:
        messages.error(request, f"创建备份失败：{exc}")
        return redirect("system_backups:list")

    result = output.getvalue().strip()
    LogEntry.objects.log_action(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(LogEntry).pk,
        object_id="backup_system",
        object_repr="系统备份",
        action_flag=CHANGE,
        change_message=f"创建系统备份。{result}".strip(),
    )
    messages.success(request, f"备份创建成功。{result}")
    return redirect("system_backups:list")


@login_required
def backup_download(request, filename):
    _require_superuser(request.user)
    if Path(filename).name != filename or not filename.endswith(".zip"):
        raise Http404
    root = Path(settings.BACKUP_DIR).resolve()
    path = (root / filename).resolve()
    if path.parent != root or not path.is_file():
        raise Http404
    LogEntry.objects.log_action(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(LogEntry).pk,
        object_id=path.name,
        object_repr=path.name,
        action_flag=CHANGE,
        change_message="下载系统备份文件。",
    )
    return FileResponse(path.open("rb"), as_attachment=True, filename=path.name)
