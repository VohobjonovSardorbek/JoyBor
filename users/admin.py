from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('phone_number', 'profile_picture')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'role', 'is_active', 'status', 'date_joined')
    list_filter = ('role', 'is_active', 'status', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Role and Status'), {'fields': ('role', 'status')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not request.user.is_superuser:
            # Remove superuser fields for non-superusers
            fieldsets = [f for f in fieldsets if f[0] != 'Permissions']
        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            # Remove superuser field from form
            if 'is_superuser' in form.base_fields:
                del form.base_fields['is_superuser']
        return form

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        # Superusers can change anyone
        if request.user.is_superuser:
            return True
        # Superadmins can't change superusers
        if request.user.is_super_admin and obj.is_superuser:
            return False
        # Superadmins can change anyone except superusers
        if request.user.is_super_admin:
            return True
        # Dormitory admins can only change students
        if request.user.is_dormitory_admin:
            return obj.is_student
        # Students can only change themselves
        return obj == request.user

    def has_delete_permission(self, request, obj=None):
        if not obj:
            return True
        # Superusers can delete anyone
        if request.user.is_superuser:
            return True
        # Superadmins can't delete superusers
        if request.user.is_super_admin and obj.is_superuser:
            return False
        # Superadmins can delete anyone except superusers
        if request.user.is_super_admin:
            return True
        # Dormitory admins can only delete students
        if request.user.is_dormitory_admin:
            return obj.is_student
        # Students can't delete anyone
        return False

    def save_model(self, request, obj, form, change):
        if change:  # If this is an update
            # Prevent role changes by non-superusers and non-superadmins
            if not (request.user.is_superuser or request.user.is_super_admin):
                obj.role = User.objects.get(pk=obj.pk).role
            # Prevent superuser creation by non-superusers
            if not request.user.is_superuser and obj.is_superuser:
                obj.is_superuser = False
            # Prevent superadmin creation by non-superusers
            if not request.user.is_superuser and obj.role == User.Role.SUPER_ADMIN:
                obj.role = User.objects.get(pk=obj.pk).role
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_super_admin:
            return qs.exclude(is_superuser=True)
        if request.user.is_dormitory_admin:
            return qs.filter(role=User.Role.STUDENT)
        return qs.filter(id=request.user.id)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    
    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        # Superusers can change anyone
        if request.user.is_superuser:
            return True
        # Superadmins can change anyone
        if request.user.is_super_admin:
            return True
        # Dormitory admins can only change students
        if request.user.is_dormitory_admin:
            return obj.user.is_student
        # Users can only change their own profile
        return obj.user == request.user

    def has_delete_permission(self, request, obj=None):
        if not obj:
            return True
        # Superusers can delete anyone
        if request.user.is_superuser:
            return True
        # Superadmins can delete anyone
        if request.user.is_super_admin:
            return True
        # Dormitory admins can only delete students
        if request.user.is_dormitory_admin:
            return obj.user.is_student
        # Users can't delete profiles
        return False
