from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("attachments/<int:pk>/download/", views.download_attachment, name="download_attachment"),
    path("projects/", views.project_list, name="projects"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("publications/", views.publication_list, name="publications"),
    path("publications/keywords/", views.keyword_list, name="keywords"),
    path("publications/<int:pk>/", views.publication_detail, name="publication_detail"),
    path("patents/", views.patent_list, name="patents"),
    path("patents/<int:pk>/", views.patent_detail, name="patent_detail"),
]
