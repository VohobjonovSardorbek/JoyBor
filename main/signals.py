from django.db.models.signals import post_save
from django.dispatch import receiver
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
from .models import Application, Payment, User, UserProfile, Notification, UserNotification
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

@receiver(post_save, sender=Notification)
def create_user_notifications(sender, instance, created, **kwargs):
    if created:
        target_type = instance.target_type

        if target_type == 'all_students':
            users = User.objects.filter(role='student')
        elif target_type == 'all_admins':
            users = User.objects.filter(role='admin')
        elif target_type == 'specific_user':
            users = [instance.target_user] if instance.target_user else []
        else:
            users = []

        user_notifications = [
            UserNotification(user=user, notification=instance) for user in users
        ]
        UserNotification.objects.bulk_create(user_notifications, ignore_conflicts=True)
