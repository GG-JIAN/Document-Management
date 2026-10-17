from django.contrib import admin
from django.urls import include, path

from accounts.views import OwnPasswordChangeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/password_change/", OwnPasswordChangeView.as_view(), name="own_password_change"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("catalog/", include("catalog.urls")),
    path("requests/", include("changes.urls")),
    path("backups/", include("system_backups.urls")),
    path("", include("members.urls")),
]

