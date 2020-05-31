from django.urls import path
from . import views

urlpatterns = [
    path("yaml/", views.yaml.as_view(), name="yml"),
    path("allgroup/", views.get_group, name="allgroup"),
    path("run/", views.run_ansible, name="run"),
    path("docker/", views.DockerServer.as_view(), name="docker"),
    path("conn-docker-server/", views.ConnDockerServer, name="conn-docker-server"),
    path("docker-images/", views.DockerGetImage.as_view(), name="docker-images"),
    path("docker-container/", views.ContainerServer.as_view(), name="docker-container"),
    path("search_image/", views.search_image, name="search_image"),
    path("container-network/", views.ContainerNetWork.as_view(), name="container-network"),
    path("run-container/", views.RunContainer, name="run-container")
]
