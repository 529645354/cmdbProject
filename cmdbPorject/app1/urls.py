from django.urls import path, re_path
from . import views

urlpatterns = [
    path('server/', views.QueryServer.as_view(), name="index"),
    path('group/', views.ServerGroup.as_view(), name="group"),
    path('manage/', views.ManageServer.as_view(), name="manage"),
    path('get-server-no-group/', views.get_no_group_server, name="no_group_server"),
    path('install_vnc/', views.install_vnc, name="install_vnc"),
    path('tasks/', views.get_tasks, name="get_tasks")
]
