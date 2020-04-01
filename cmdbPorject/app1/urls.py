from django.urls import path,re_path
from . import views

urlpatterns = [
    path('server/',views.QueryServer.as_view(), name="index"),
]
