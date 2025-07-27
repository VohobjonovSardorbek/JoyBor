from django.db.models.signals import post_save
from django.dispatch import receiver
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
from .models import Application, Payment, User, UserProfile, Notification
from django.utils import timezone


# from .serializers import ApplicationSerializer


@receiver(post_save, sender=Payment)
def update_student_status_on_payment(sender, instance, created, **kwargs):
    if created:
        student = instance.student
        # Faqat shu studentga bog'langan paymentlarni tekshiramiz
        last_payment = student.payments.order_by('-valid_until').first()
        if last_payment and last_payment.valid_until >= timezone.now().date():
            student.status = 'haqdor'
            student.save()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=Application)
def create_notification(sender, instance, created, **kwargs):
    if created:
        dormitory_admin = instance.dormitory.admin  # Dormitorydagi adminni olamiz
        if dormitory_admin:  # Agar admin mavjud bo‘lsa
            Notification.objects.create(
                user=dormitory_admin,
                message=f"Yangi ariza tushdi: {instance.name} sizning yotoqxonangiz uchun."
            )


# @receiver(post_save, sender=Application)
# def application_created(sender, instance, created, **kwargs):
#     if created:
#         channel_layer = get_channel_layer()
#         data = ApplicationSerializer(instance).data
#         admin_id = instance.dormitory.admin.id
#         group_name = f"dormitory_admin_{admin_id}"
#         async_to_sync(channel_layer.group_send)(
#             group_name,
#             {
#                 "type": "send_application",
#                 "application": data,
#             }
#         )
