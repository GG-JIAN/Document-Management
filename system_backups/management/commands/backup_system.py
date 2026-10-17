import os
import shutil
import sqlite3
import subprocess
import tempfile
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Create a ZIP backup containing the database and uploaded media files."

    def handle(self, *args, **options):
        backup_dir = Path(settings.BACKUP_DIR)
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        archive_path = backup_dir / f"lab_backup_{timestamp}.zip"

        with tempfile.TemporaryDirectory(prefix="lab_backup_", dir=backup_dir) as temp_name:
            staging = Path(temp_name)
            database_file = self._dump_database(staging)
            media_dir = staging / "media"
            self._copy_media(media_dir, backup_dir)
            temp_archive = archive_path.with_suffix(".zip.tmp")
            try:
                with zipfile.ZipFile(temp_archive, "w", zipfile.ZIP_DEFLATED) as archive:
                    archive.write(database_file, arcname=database_file.name)
                    if media_dir.exists():
                        for path in media_dir.rglob("*"):
                            if path.is_file():
                                archive.write(path, arcname=path.relative_to(staging).as_posix())
                temp_archive.replace(archive_path)
            except Exception:
                temp_archive.unlink(missing_ok=True)
                raise

        self.stdout.write(self.style.SUCCESS(f"Created backup: {archive_path}"))

    def _dump_database(self, staging):
        database = settings.DATABASES["default"]
        engine = database["ENGINE"]
        if engine.endswith("sqlite3"):
            source_path = Path(database["NAME"])
            if not source_path.is_file():
                raise CommandError(f"SQLite database not found: {source_path}")
            target_path = staging / "database.sqlite3"
            source = sqlite3.connect(source_path)
            target = sqlite3.connect(target_path)
            try:
                source.backup(target)
            except sqlite3.Error as exc:
                raise CommandError(f"SQLite backup failed: {exc}") from exc
            finally:
                source.close()
                target.close()
            return target_path

        if engine.endswith("postgresql"):
            target_path = staging / "database.dump"
            executable = os.environ.get("PG_DUMP_PATH", "pg_dump")
            command = [executable, "--format=custom", "--no-owner", "--file", str(target_path)]
            if database.get("HOST"):
                command.extend(("--host", str(database["HOST"])))
            if database.get("PORT"):
                command.extend(("--port", str(database["PORT"])))
            if database.get("USER"):
                command.extend(("--username", str(database["USER"])))
            command.extend(("--dbname", str(database["NAME"])))
            env = os.environ.copy()
            if database.get("PASSWORD"):
                env["PGPASSWORD"] = str(database["PASSWORD"])
            try:
                subprocess.run(command, check=True, env=env, capture_output=True, text=True)
            except FileNotFoundError as exc:
                raise CommandError("pg_dump 未找到，请安装 PostgreSQL 客户端或设置 PG_DUMP_PATH。") from exc
            except subprocess.CalledProcessError as exc:
                raise CommandError(f"PostgreSQL backup failed: {exc.stderr.strip()}") from exc
            return target_path

        raise CommandError(f"Unsupported database engine: {engine}")

    @staticmethod
    def _copy_media(target_dir, backup_dir):
        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.exists():
            return
        target_dir.mkdir(parents=True, exist_ok=True)
        backup_root = backup_dir.resolve()
        for source in media_root.rglob("*"):
            if not source.is_file():
                continue
            resolved = source.resolve()
            if resolved == backup_root or backup_root in resolved.parents:
                continue
            destination = target_dir / source.relative_to(media_root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
