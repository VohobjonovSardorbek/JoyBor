from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
from .models import Application, Payment, User, UserProfile, Notification, UserNotification, ApplicationNotification, Task, Floor, Room, Student
from django.utils import timezone
from django.db import transaction
from rest_framework import serializers


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=Application)
def create_application_notification(sender, instance, created, **kwargs):
    if created:
        dormitory_admin = instance.dormitory.admin
        if dormitory_admin:
            ApplicationNotification.objects.create(
                user=dormitory_admin,
                message=f"Yangi ariza tushdi: {instance.name} sizning yotoqxonangiz uchun."
            )

    # Ariza egasiga status o'zgarishi haqida xabar yuborish
    if not created and instance.status in ['APPROVED', 'REJECTED']:
        if instance.user:
            if instance.status == 'APPROVED':
                msg = f"Arizangiz tasdiqlandi: {instance.dormitory.name}."
            else:
                msg = f"Arizangiz rad etildi: {instance.dormitory.name}."
            ApplicationNotification.objects.create(
                user=instance.user,
                message=msg
            )


@receiver(post_save, sender=Payment)
def update_student_status_after_payment(sender, instance, **kwargs):
    """
    Har safar Payment qo‘shilganda yoki yangilanganda
    talabaning statusini tekshirish va kerak bo‘lsa yangilash.
    """

    student = instance.student
    today = timezone.now().date()

    # 1️⃣ Joylashish jarayonida bo‘lsa
    if student.placement_status == 'Qabul qilindi':
        new_status = 'Tekshirilmaydi'
    else:
        # 2️⃣ Oxirgi tasdiqlangan to‘lovni olish
        last_payment = student.payments.filter(status='APPROVED').order_by('-valid_until').first()

        if not last_payment or not last_payment.valid_until or last_payment.valid_until < today:
            new_status = 'Qarzdor'
        else:
            new_status = 'Haqdor'

    # 3️⃣ Faqat status o‘zgarganda saqlash
    if student.status != new_status:
        student.status = new_status
        student.save(update_fields=['status'])

    # 4️⃣ Agar yangi payment tasdiqlangan bo‘lsa — application egasiga xabar yuborish
    if instance.status == 'APPROVED' and student.passport:
        try:
            related_app = (
                Application.objects
                .filter(passport=student.passport)
                .order_by('-created_at')
                .select_related('user')
                .first()
            )
            if related_app and related_app.user:
                ApplicationNotification.objects.create(
                    user=related_app.user,
                    message=f"Sizning nomingizga {instance.amount} so'm to‘lov tasdiqlandi."
                )
        except ObjectDoesNotExist:
            # Agar Application topilmasa, signal jim o'tadi
            pass
        except Exception as e:
            # Xatolikni loglash mumkin
            print(f"Notification yaratishda xatolik: {e}")

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


@receiver(post_save, sender=Task)
def create_task_reminder(sender, instance, created, **kwargs):
    """
    Task yaratilganda yoki yangilanganda reminder yaratish
    """
    if created and instance.reminder_date and not instance.reminder_sent:
        # Reminder vaqti kelganda foydalanuvchiga xabar yuborish
        if instance.reminder_date <= timezone.now():
            ApplicationNotification.objects.create(
                user=instance.user,
                message=f"Eslatma: {instance.description} - Bu vazifa bajarilishi kerak!"
            )
            instance.reminder_sent = True
            instance.save(update_fields=['reminder_sent'])


@receiver(pre_save, sender=Floor)
def check_floor_name_uniqueness(sender, instance, **kwargs):
    """
    Floor nomi yotoqxona ichida unique bo'lishini tekshirish
    """
    if instance.pk:  # Yangilash holatida
        try:
            existing_floor = Floor.objects.get(pk=instance.pk)
            if existing_floor.name != instance.name:
                # Nom o'zgartirilgan, tekshirish kerak
                if Floor.objects.filter(dormitory=instance.dormitory, name=instance.name).exclude(pk=instance.pk).exists():
                    raise serializers.ValidationError(f"'{instance.name}' nomli qavat sizning yotoqxonangizda allaqachon mavjud!")
        except Floor.DoesNotExist:
            pass
    else:  # Yangi yaratish holatida
        if Floor.objects.filter(dormitory=instance.dormitory, name=instance.name).exists():
            raise serializers.ValidationError(f"'{instance.name}' nomli qavat sizning yotoqxonangizda allaqachon mavjud!")


@receiver(pre_save, sender=Room)
def check_room_name_uniqueness(sender, instance, **kwargs):
    """
    Room nomi floor ichida unique bo'lishini tekshirish
    """
    if instance.pk:  # Yangilash holatida
        try:
            existing_room = Room.objects.get(pk=instance.pk)
            if existing_room.name != instance.name:
                # Nom o'zgartirilgan, tekshirish kerak
                if Room.objects.filter(floor=instance.floor, name=instance.name).exclude(pk=instance.pk).exists():
                    raise serializers.ValidationError(f"'{instance.name}' nomli xona bu qavatda allaqachon mavjud!")
        except Room.DoesNotExist:
            pass
    else:  # Yangi yaratish holatida
        if Room.objects.filter(floor=instance.floor, name=instance.name).exists():
            raise serializers.ValidationError(f"'{instance.name}' nomli xona bu qavatda allaqachon mavjud!")



ROOM_STATUS_AVAILABLE = 'AVAILABLE'
ROOM_STATUS_PARTIALLY = 'PARTIALLY_OCCUPIED'
ROOM_STATUS_FULL = 'FULLY_OCCUPIED'
PLACEMENT_STATUS_DONE = 'Joylashdi'
PLACEMENT_STATUS_PENDING = 'Qabul qilindi'


def update_room_status(room: Room):
    """Xonadagi currentOccupancy va statusni yangilaydi"""
    if not room:
        return
    current_count = room.students.count()
    room.currentOccupancy = current_count

    if current_count == 0:
        room.status = ROOM_STATUS_AVAILABLE
    elif current_count < room.capacity:
        room.status = ROOM_STATUS_PARTIALLY
    else:
        room.status = ROOM_STATUS_FULL

    room.save(update_fields=['currentOccupancy', 'status'])


@receiver(pre_save, sender=Student)
def track_old_room(sender, instance, **kwargs):
    """Student room o'zgarganda eski roomni ham yangilash uchun"""
    if instance.pk:
        try:
            old_instance = Student.objects.get(pk=instance.pk)
            instance._old_room = old_instance.room
        except Student.DoesNotExist:
            instance._old_room = None


@receiver(post_save, sender=Student)
def update_room_on_save(sender, instance, created, **kwargs):
    """
    Student qo'shilganda yoki update qilinganda xonani yangilash
    """
    # placement_status
    if instance.floor and instance.room:
        if instance.placement_status != PLACEMENT_STATUS_DONE:
            Student.objects.filter(pk=instance.pk).update(
                placement_status=PLACEMENT_STATUS_DONE
            )

    # Eski room yangilanishi kerak (agar student ko'chirilgan bo'lsa)
    old_room = getattr(instance, "_old_room", None)
    if old_room and old_room != instance.room:
        update_room_status(old_room)

    # Yangi room yangilanishi kerak
    if instance.room:
        update_room_status(instance.room)


@receiver(post_delete, sender=Student)
def update_room_on_delete(sender, instance, **kwargs):
    """Student o‘chirib tashlanganda xonani yangilash"""
    if instance.room:
        update_room_status(instance.room)

