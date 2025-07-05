import json
from channels.generic.websocket import AsyncWebsocketConsumer
from main.models import Dormitory

class ApplicationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            dormitory = Dormitory.objects.filter(admin=user).first()
            if dormitory:
                self.group_name = f"dormitory_admin_{dormitory.id}"
                await self.channel_layer.group_add(self.group_name, self.channel_name)
                await self.accept()
                return
        await self.close()

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if user.is_authenticated:
            dormitory = Dormitory.objects.filter(admin=user).first()
            if dormitory:
                await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_application(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_application",
            "application": event["application"]
        }))
