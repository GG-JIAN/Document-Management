from django.urls import path

from . import views

app_name = "members"

urlpatterns = [
    path("", views.member_list, name="list"),
    path("materials/", views.materials_placeholder, name="materials"),
    path("members/<int:pk>/", views.member_detail, name="detail"),
]

