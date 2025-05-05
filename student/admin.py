from django.contrib import admin
from .models import Student, Application, ApplicationDocument

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'university', 'faculty', 'course', 'dormitory', 'room')
    list_filter = ('university', 'faculty', 'course', 'dormitory')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'student_id')
    raw_id_fields = ('user', 'university', 'dormitory', 'room')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'dormitory', 'preferred_room_type', 'status', 'created_at')
    list_filter = ('status', 'dormitory', 'created_at')
    search_fields = ('student__user__username', 'student__student_id', 'dormitory__name')
    raw_id_fields = ('student', 'dormitory', 'reviewed_by')

@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ('application', 'document_type', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('application__student__user__username', 'application__student__student_id')
    raw_id_fields = ('application',)
