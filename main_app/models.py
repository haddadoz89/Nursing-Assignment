# In main_app/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


# The final, all-in-one model for a staff member.
class User(AbstractUser):
    class Role(models.TextChoices):
        NURSE = 'NURSE', 'Nurse'
        MAS = 'MAS', 'MAS (Auxiliary)'
        NURSE_MANAGER = 'MANAGER', 'Nurse Manager'

    # --- Authentication Fields ---
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="The part of the email before @phc.gov.bh"
    )
    email = models.EmailField(blank=True)

    phone_number = PhoneNumberField(
        unique=True,
        region='BH',
        help_text="Must be a unique Bahraini phone number."
    )

    # --- Profile Fields ---
    employee_id = models.IntegerField(unique=True, blank=True, null=True)
    role = models.CharField(max_length=7, choices=Role.choices, default=Role.NURSE)

    # --- Settings for Login ---
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

    @property
    def full_email(self):
        return f"{self.username}@phc.gov.bh"

    def __str__(self):
        return self.get_full_name() or self.username

# --- Shift and Task Models ---

class ShiftType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return self.name


class Assignment(models.Model):
    name = models.CharField(max_length=200, unique=True)
    def __str__(self): return self.name

class SubAssignment(models.Model):
    name = models.CharField(max_length=200, unique=True)
    def __str__(self): return self.name

class Clinic(models.Model):
    name = models.CharField(max_length=200, unique=True)
    def __str__(self): return self.name
    class Meta:
        verbose_name_plural = "Clinics"

class EmergencyRole(models.Model):
    name = models.CharField(max_length=200, unique=True)
    def __str__(self): return self.name


class Shift(models.Model):
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shifts')
    date = models.DateField()
    shift_type = models.ForeignKey(ShiftType, on_delete=models.PROTECT, related_name='shifts')

    assignments = models.ManyToManyField(Assignment, blank=True)
    sub_assignments = models.ManyToManyField(SubAssignment, blank=True)
    clinics = models.ManyToManyField(Clinic, blank=True)
    emergency_roles = models.ManyToManyField(EmergencyRole, blank=True)

    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Shift for {self.staff} on {self.date} ({self.shift_type.name})"

    class Meta:
        unique_together = ('staff', 'date', 'shift_type')

class Rotation(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., 'Week A Rotation', '4 On / 2 Off'")
    length_in_days = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class RotationDay(models.Model):
    rotation = models.ForeignKey(Rotation, on_delete=models.CASCADE, related_name='days')
    day_number = models.PositiveIntegerField(help_text="The day in the rotation sequence (e.g., 1, 2, 3...)")
    shift_type = models.ForeignKey(ShiftType, on_delete=models.CASCADE, null=True, blank=True)
    is_day_off = models.BooleanField(default=False)

    class Meta:
        ordering = ['day_number']
        unique_together = ('rotation', 'day_number')

    def __str__(self):
        if self.is_day_off:
            return f"Day {self.day_number}: Off"
        return f"Day {self.day_number}: {self.shift_type.name}"

class MonthlyTask(models.Model):
    """A type of task that is assigned monthly, e.g., 'Inventory Check'."""
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

class MonthlyAssignment(models.Model):
    """Links a staff member to a monthly task for a specific DATE RANGE."""
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_assignments')
    task = models.ForeignKey(MonthlyTask, on_delete=models.CASCADE, related_name='assignments')
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True, help_text="Explain why this assignment is split, if applicable.")

    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.task.name} ({self.start_date} to {self.end_date})"