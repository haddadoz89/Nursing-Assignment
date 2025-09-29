# In main_app/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Shift, ShiftType, Assignment, SubAssignment, Clinic, EmergencyRole, Rotation, RotationDay

# We need to customize the User admin to show our new fields
class CustomUserAdmin(UserAdmin):
    # Add our custom fields to the display and editing forms
    list_display = ('username', 'first_name', 'last_name', 'role', 'phone_number')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Profile Info', {'fields': ('role', 'employee_id', 'phone_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Profile Info', {'fields': ('first_name', 'last_name', 'role', 'employee_id', 'phone_number')}),
    )

class RotationDayInline(admin.TabularInline):
    model = RotationDay
    extra = 1


class RotationAdmin(admin.ModelAdmin):
    inlines = [RotationDayInline]
    list_display = ('name', 'length_in_days')

# Register your models here
admin.site.register(User, CustomUserAdmin)
admin.site.register(Shift)
admin.site.register(ShiftType)
admin.site.register(Assignment)
admin.site.register(SubAssignment)
admin.site.register(Clinic)
admin.site.register(EmergencyRole)
admin.site.register(Rotation, RotationAdmin)