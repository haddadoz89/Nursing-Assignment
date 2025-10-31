# In main_app/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Committee, User, Shift, ShiftType, Assignment, SubAssignment, Clinic, EmergencyRole, Rotation, RotationDay, MonthlyTask, MonthlyAssignment, AssignmentGroup

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'phone_number','assignment_group', 'is_active')
    fieldsets = list(UserAdmin.fieldsets) + [
        ('Custom Profile Info', {'fields': ('role', 'employee_id', 'phone_number', 'assignment_group')}),
    ]
    add_fieldsets = list(UserAdmin.add_fieldsets) + [
        ('Custom Profile Info', {'fields': ('first_name', 'last_name', 'role', 'employee_id', 'phone_number', 'assignment_group')}),
    ]

class RotationDayInline(admin.TabularInline):
    model = RotationDay
    extra = 1


class RotationAdmin(admin.ModelAdmin):
    inlines = [RotationDayInline]
    list_display = ('name', 'length_in_days')

class MonthlyAssignmentAdmin(admin.ModelAdmin):
    list_display = ('staff', 'task', 'group', 'committee', 'start_date', 'end_date', 'status') 
    list_filter = ('group', 'committee', 'staff', 'task', 'start_date', 'status') 
    search_fields = ('staff__first_name', 'staff__last_name', 'task__name', 'group__name', 'committee__name')

admin.site.register(User, CustomUserAdmin)
admin.site.register(Shift)
admin.site.register(ShiftType)
admin.site.register(Assignment)
admin.site.register(SubAssignment)
admin.site.register(Clinic)
admin.site.register(EmergencyRole)
admin.site.register(Rotation, RotationAdmin)
admin.site.register(MonthlyTask)
admin.site.register(MonthlyAssignment, MonthlyAssignmentAdmin)
admin.site.register(AssignmentGroup) # Register new model
admin.site.register(Committee)