from channels.generic.websocket import WebsocketConsumer
import json


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        print(self.scope)
        self.accept()

    def disconnect(self, close_code):
        self.close()

    def receive(self, text_data):
        print(text_data)
        print("*" * 10)
        self.send(text_data=json.dumps({
            'message': text_data
        }))
        self.send(text_data=json.dumps({
            "aa": "aaa"
        }))
        self.close(code=3600)
