import json
from channels.generic.websocket import WebsocketConsumer
import serverMon.mon
from status.status import Status


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        print(self.scope)
        self.accept()

    def disconnect(self, close_code):
        self.close()

    def receive(self, text_data=None, bytes_data=None):
        try:
            id = int(text_data)
        except ValueError:
            self.send(json.dumps({"data": Status.dataError}))
        else:
            if id == 1:
                self.send(json.dumps(
                    {"data": 200, "content": {"mem": serverMon.mon.Mon.mem(), "cpu": serverMon.mon.Mon.cpu(),
                                              "network": serverMon.mon.Mon.net(),
                                              "innetwork": serverMon.mon.Mon.inputnet(),
                                              "disk": serverMon.mon.Mon.disk()}}))
