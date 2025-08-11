from django.db.models.signals import post_save
from django.dispatch import receiver
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
from .models import Application, Payment, User, UserProfile, Notification
from django.utils import timezone


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


@receiver(post_save, sender=Payment)
def update_student_status_after_payment(sender, instance, created, **kwargs):
    """
    Yangi payment qo‘shilganda talaba statusini avtomatik yangilash.
    """
    if not created or instance.status != 'APPROVED':
        return  # Faqat yangi va APPROVED to‘lovlar uchun ishlaydi

    student = instance.student
    today = timezone.now().date()

    # 1. Joylashish jarayonida bo‘lsa
    if student.placement_status == 'Qabul qilindi':
        new_status = 'Tekshirilmaydi'
    else:
        # 2. Oxirgi APPROVED to‘lovni olish
        last_payment = student.payments.filter(status='APPROVED').order_by('-valid_until').first()
        if not last_payment or not last_payment.valid_until or last_payment.valid_until < today:
            new_status = 'Qarzdor'
        else:
            new_status = 'Haqdor'

    # 3. Faqat status o‘zgarganda saqlash
    if student.status != new_status:
        student.status = new_status
        student.save(update_fields=['status'])

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
