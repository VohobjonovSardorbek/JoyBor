from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Application
from .serializers import ApplicationSerializer

@receiver(post_save, sender=Application)
def application_created(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        data = ApplicationSerializer(instance).data
        admin_id = instance.dormitory.admin.id
        group_name = f"dormitory_admin_{admin_id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_application",
                "application": data,
            }
        )
