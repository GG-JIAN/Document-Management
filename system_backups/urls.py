from django.urls import path

from . import views

app_name = "system_backups"

urlpatterns = [
    path("", views.backup_list, name="list"),
    path("create/", views.backup_create, name="create"),
    path("<str:filename>/download/", views.backup_download, name="download"),
]
