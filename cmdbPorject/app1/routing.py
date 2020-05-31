from django.conf.urls import url

from app1 import consumers

websocket_urlpatterns = [
    url(r'^deploy$', consumers.ChatConsumer)  # consumers.DeployResult 是该路由的消费者
]
