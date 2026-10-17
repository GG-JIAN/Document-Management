from django.urls import path

from . import views

app_name = "changes"

urlpatterns = [
    path("", views.request_list, name="list"),
    path("<int:pk>/attachment/", views.download_request_attachment, name="download_attachment"),
    path("new/", views.create_member_request, name="new"),
    path("new/<str:kind>/", views.create_upload_request, name="upload"),
    path("new/publication/<int:pk>/edit/", views.create_publication_update_request, name="edit_publication"),
    path("<int:pk>/review/", views.review_member_request, name="review"),
]
