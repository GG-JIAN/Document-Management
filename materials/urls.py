from django.urls import path

from . import views

app_name = "materials"

urlpatterns = [
    path("", views.material_list, name="list"),
    path("download/", views.download_latest_excel, name="download"),
    path("compare/", views.compare_materials, name="compare"),
    path("<int:pk>/", views.material_detail, name="detail"),
]
